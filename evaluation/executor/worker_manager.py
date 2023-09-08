from evaluation.executor.task_pool import *
from evaluation.internal.torch_module_adapter import *

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
        self.job_id_model_adapter_map = {}
        self.job_id_agg_weight_map = {}
        self.job_id_agg_cnt = {}
        self.logger = logger
        self.lock = asyncio.Lock()

        self._setup_seed()

        self.config = config
        self.device = config["cuda_device"] if config["use_cuda"] else "cpu"

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
            if job_id in self.job_id_model_adapter_map:
                del self.job_id_model_adapter_map[job_id]
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

        model_adapter = Torch_model_adapter(model,
                                            optimizer=TorchServerOptimizer(args["gradient_policy"], args, self.device))
            # model_adapter.set_weights(model_weights)
        model_size = sys.getsizeof(pickle.dumps(model_adapter)) / 1024.0 * 8.  # kbits

        async with self.lock:
            self.job_id_model_adapter_map[job_id] = model_adapter
            self.job_id_agg_weight_map[job_id] = []
            self.job_id_agg_cnt[job_id] = 0

        # broadcast
        job_meta = {"dataset": dataset_name}
        job_info_msg = executor_pb2.job_info(
            job_id=job_id,
            job_meta=pickle.dumps(job_meta)
        )
        for worker_stub in self.worker_stub_dict.values():
            await worker_stub.INIT(job_info_msg)

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
                task_data = self.job_id_model_adapter_map[job_id].get_model()

                job_task_msg = executor_pb2.job_task_info(
                    job_id=job_id,
                    client_id=client_id,
                    round=0,
                    event=event,
                    task_meta=pickle.dumps(args),
                    task_data=pickle.dumps(task_data)
                )

            await self.worker_stub_dict[cur_worker].TASK_REGIST(job_task_msg)

            ping_num = 0
            while True:
                await asyncio.sleep(5)
                ping_msg = executor_pb2.job_task_info(
                    job_id=job_id,
                    client_id=client_id,
                    round=0,
                    event=event,
                    task_meta=pickle.dumps(DUMMY_RESPONSE),
                    task_data=pickle.dumps(DUMMY_RESPONSE)
                )
                task_result_msg = await self.worker_stub_dict[cur_worker].PING(ping_msg)

                if task_result_msg.ack:
                    results = pickle.loads(task_result_msg.result)
                    break

                ping_num += 1
                if ping_num >= 50:
                    self.logger(f"Unable to retrieve job {job_id} client {client_id} {event}", ERROR)
                    return None

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
            async with self.lock:
                try:
                    if abort:
                        self.job_id_agg_cnt[job_id] = 0
                        self.job_id_agg_weight_map[job_id] = None
                        return None
                    agg_weight = self.job_id_agg_weight_map[job_id]
                    if self.job_id_agg_cnt[job_id] > 0:
                        agg_weight = [np.divide(weight, self.job_id_agg_cnt[job_id]) for weight in agg_weight]

                        self.job_id_model_adapter_map[job_id].set_weights(copy.deepcopy(agg_weight))
                    results = {
                        "agg_number": self.job_id_agg_cnt[job_id]
                    }
                    self.job_id_agg_cnt[job_id] = 0
                    self.job_id_agg_weight_map[job_id] = None
                except Exception as e:
                    self.logger.print(e, ERROR)

            results = {AGGREGATE: results}

        return results
            

