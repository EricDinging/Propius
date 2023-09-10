from evaluation.executor.task_pool import *
import numpy as np
import random
import torch
import asyncio
import sys
import pickle
import grpc
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc


class Worker_manager:
    def __init__(self, config, logger):
        """Init worker class

        Args:
            config:
        """
        self.job_id_agg_weight_map = {}
        self.job_id_agg_cnt = {}
        self.logger = logger
        self.lock = asyncio.Lock()
        self._setup_seed()
        self.config = config
        self.worker_num = len(config["worker"])
        self.worker_addr_list = config["worker"]
        self.worker_channel_dict = {}
        self.worker_stub_dict = {}
        self._connect_worker()
        self.cur_worker = 0

    def _connect_worker(self):
        channel_options = [
            ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH)
        ]
        for worker_id, worker_addr in enumerate(self.worker_addr_list):
            worker_ip = worker_addr["ip"] if not self.config["use_docker"] else f"worker_{worker_id}"
            worker_port = worker_addr["port"]
            self.worker_channel_dict[worker_id] = grpc.aio.insecure_channel(f"{worker_ip}:{worker_port}", options=channel_options)
            self.worker_stub_dict[worker_id] = executor_pb2_grpc.WorkerStub(
                self.worker_channel_dict[worker_id]
            )
            self.logger.print(f"Worker manager: connecting to worker {worker_id} at {worker_ip}:{worker_port}", INFO)
    
    async def _disconnect(self):
        for worker_channel in self.worker_channel_dict.values():
            await worker_channel.close()

    def _setup_seed(self, seed=1):
        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)


    async def remove_job(self, job_id: int):
        async with self.lock:
            if job_id in self.job_id_agg_weight_map:
                del self.job_id_agg_weight_map[job_id]
                del self.job_id_agg_cnt[job_id]
        
        job_info_msg = executor_pb2.job_info(
            job_id=job_id,
            job_meta=pickle.dumps(DUMMY_RESPONSE)
        )

        # broadcast
        for worker_stub in self.worker_stub_dict.values():
            await worker_stub.REMOVE(job_info_msg)


    async def init_job(self, job_id: int, dataset_name: str, model_name: str, args: dict)->float:
        model = None
        if model_name == "resnet18":
            from evaluation.internal.models.specialized.resnet_speech import resnet18
            model = resnet18(
                num_classes=out_put_class[dataset_name],
                in_channels=1
            )
        elif model_name == "mobilenet":
            from evaluation.internal.models.specialized.resnet_speech import \
            mobilenet_v2
            model = mobilenet_v2(num_classes=out_put_class[dataset_name])

        model_size = sys.getsizeof(pickle.dumps(model)) / 1024.0 * 8.  # kbits

        # broadcast
        
        job_init_msg = executor_pb2.job_init(
            job_id=job_id,
            job_meta=pickle.dumps(args),
            model_weight=pickle.dumps(model)
        )

        for worker_stub in self.worker_stub_dict.values():
            await worker_stub.INIT(job_init_msg)
        
        async with self.lock:
            self.job_id_agg_weight_map[job_id] = []
            self.job_id_agg_cnt[job_id] = 0
        
        self.logger.print(f"Worker manager: init job {job_id} success", INFO)

        return model_size
        
    async def heartbeat_routine(self):
        try:
            while True:
                await asyncio.sleep(10)
                
                status_list = []

                for worker_stub in self.worker_stub_dict.values():
                    worker_status_msg = await worker_stub.HEART_BEAT(executor_pb2.empty())
                    status_list.append(worker_status_msg.task_size)
                
                # self.cur_worker = status_list.index(min(status_list))
                self.logger.print(f"Worker manager: current worker {self.cur_worker}", PRINT)
        except asyncio.CancelledError:
            pass

    async def execute(self, event: str, job_id: int, client_id: int, args: dict, abort: bool = False)->dict:
        if event == CLIENT_TRAIN or event == MODEL_TEST:
            async with self.lock:
                self.cur_worker = (self.cur_worker + 1) % self.worker_num

                cur_worker = self.cur_worker
                job_task_msg = executor_pb2.job_task_info(
                    job_id=job_id,
                    client_id=client_id,
                    round=0,
                    event=event,
                    task_meta=pickle.dumps(args),
                )

            await self.worker_stub_dict[cur_worker].TASK_REGIST(job_task_msg)

            ping_num = 0
            await asyncio.sleep(0.01)
            while True:
                ping_msg = executor_pb2.job_task_info(
                    job_id=job_id,
                    client_id=client_id,
                    round=0,
                    event=event,
                    task_meta=pickle.dumps(DUMMY_RESPONSE),
                )
                task_result_msg = await self.worker_stub_dict[cur_worker].PING(ping_msg)

                if task_result_msg.ack:
                    results = pickle.loads(task_result_msg.result)
                    break

                ping_num += 1
                if ping_num >= 30:
                    self.logger.print(f"Unable to retrieve job {job_id} client {client_id} {event}", ERROR)
                    return None
                await asyncio.sleep(0.5)

            if event == CLIENT_TRAIN:
                model_param = results["model_weight"]
                async with self.lock:
                    try:
                        self.job_id_agg_cnt[job_id] += 1

                        agg_weight = self.job_id_agg_weight_map[job_id]
                        if self.job_id_agg_cnt[job_id] == 1:
                            agg_weight = model_param
                        else:
                            agg_weight = [weight + model_param[i] for i, weight in enumerate(agg_weight)]
                        self.job_id_agg_weight_map[job_id] = agg_weight
                    except Exception as e:
                        self.logger.print(e, ERROR)

                del results["model_weight"]
                results = {CLIENT_TRAIN+str(client_id): results}
        

        elif event == AGGREGATE:
            results = None
            async with self.lock:
                try:
                    if abort:
                        self.job_id_agg_cnt[job_id] = 0
                        self.job_id_agg_weight_map[job_id] = None
                        return None
                    agg_weight = self.job_id_agg_weight_map[job_id]
                    if self.job_id_agg_cnt[job_id] > 0:
                        agg_weight = [np.divide(weight, self.job_id_agg_cnt[job_id]) for weight in agg_weight]

                        job_weight_msg = executor_pb2.job_weight(
                            job_id = job_id,
                            job_data = pickle.dumps(agg_weight)
                        )

                        for worker_id, worker_stub in self.worker_stub_dict.items():
                            ack_msg = await worker_stub.UPDATE(job_weight_msg)
                            if not ack_msg.ack:
                                self.logger.print(f"Update model weight to worker {worker_id} failed", ERROR)

                    results = {
                        "agg_number": self.job_id_agg_cnt[job_id]
                    }
                    self.job_id_agg_cnt[job_id] = 0
                    self.job_id_agg_weight_map[job_id] = None
                except Exception as e:
                    self.logger.print(e, ERROR)

            results = {AGGREGATE: results}

        return results
            

