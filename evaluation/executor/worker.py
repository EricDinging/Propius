import asyncio
import yaml
import grpc
import pickle
import sys
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc
from evaluation.commons import *
from evaluation.executor.internal.torch_module_adapter import *
from evaluation.executor.internal.dataset_handler import *
from evaluation.executor.internal.test_helper import *
from collections import deque
from typing import List

import torch
from torch.autograd import Variable
import numpy as np
import random

_cleanup_coroutines = []

class Worker(executor_pb2_grpc.WorkerServicer):
    def __init__(self, id: int, config: dict):
        self.id = id
        
        if id >= len(config["worker"]):
            raise ValueError("Invalid worker ID")
        
        self.ip = config["worker"][id]["ip"]
        self.port = config["worker"][id]["port"]
        device = config["worker"][id]["device"] if config["use_cuda"] else "cpu"
        self.device = torch.device(device)
        print(f"Worker {self.id}: Use {self.device}")

        self.lock = asyncio.Lock()
        
        self.job_id_data_map = {}
        self.data_partitioner_dict = {}
        self.test_data_partition_dict = {}
        self.data_partitioner_ref_cnt_dict = {}

        self.task_to_do = deque()
        self.task_finished = {}

        self._completed_steps = 0
        self._epoch_train_loss = 1e-4

        self._setup_seed()
        self.config = config

    def _setup_seed(self, seed=1):
        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)

    def _get_criterion(self, conf):
        criterion = None
        criterion = torch.nn.CrossEntropyLoss(reduction='none').to(device=self.device)
        return criterion
    
    def _get_optimizer(self, model, conf):
        optimizer = torch.optim.SGD(
            model.parameters(), lr=conf['learning_rate'],
            momentum=0.9, weight_decay=5e-4
        )
        return optimizer
    
    def _train_step(self, client_data: DataLoader, conf: dict, model: Torch_model_adapter, optimizer, criterion):
        for data_pair in client_data:
            (data, target) = data_pair
            data = Variable(data).to(device=self.device)
            target = Variable(target).to(device=self.device)

            output = model(data)
            loss = criterion(output, target)

            loss_list = loss.tolist()
            loss = loss.mean()

            temp_loss = sum(loss_list) / float(len(loss_list))

            if self._completed_steps < len(client_data):
                if self._epoch_train_loss == 1e-4:
                    self._epoch_train_loss = temp_loss
                else:
                    self._epoch_train_loss = (1. - conf['loss_decay']) * \
                        self._epoch_train_loss + conf['loss_decay'] * temp_loss
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            self._completed_steps += 1

            if self._completed_steps == conf['local_steps']:
                break

    async def INIT(self, request, context):
        job_id = request.job_id
        job_meta = pickle.loads(request.job_meta)
        dataset_name = job_meta["dataset"]

        async with self.lock:
            self.job_id_data_map[job_id] = dataset_name

            if dataset_name not in self.data_partitioner_dict:
                if dataset_name == "femnist":
                    from fedscale.dataloaders.femnist import FEMNIST
                    from fedscale.dataloaders.utils_data import get_data_transform

                    train_transform, test_transform = get_data_transform("mnist")
                    train_dataset = FEMNIST(
                        self.config['femnist_data_dir'],
                        dataset='train',
                        transform=train_transform
                    )
                    test_dataset = FEMNIST(
                        self.config['femnist_data_dir'],
                        dataset='test',
                        transform=test_transform
                    )
                    
                    train_partitioner = Data_partitioner(data=train_dataset, num_of_labels=out_put_class[dataset_name])
                    train_partitioner.partition_data_helper(0, data_map_file=self.config['femnist_data_map_file'])
                    self.data_partitioner_dict[dataset_name] = train_partitioner
                   
                    test_partitioner = Data_partitioner(data=test_dataset, num_of_labels=out_put_class[dataset_name])
                    test_partitioner.partition_data_helper(0, data_map_file=self.config['femnist_test_data_map_file'])
                    self.test_data_partition_dict[dataset_name] = test_partitioner
                
                self.data_partitioner_ref_cnt_dict[dataset_name] = 0
            
            self.data_partitioner_ref_cnt_dict[dataset_name] += 1
            print(f"Worker {self.id}: recieve job {job_id} init")

        return executor_pb2.ack(ack=True)
    
    async def REMOVE(self, request, context):
        job_id = request.job_id
        async with self.lock:
            if job_id in self.job_id_data_map:
                dataset_name = self.job_id_data_map[job_id]
                del self.job_id_data_map[job_id]
                self.data_partitioner_ref_cnt_dict[dataset_name] -= 1
                if self.data_partitioner_ref_cnt_dict[dataset_name] == 0:
                    del self.data_partitioner_dict[dataset_name]
                    del self.test_data_partition_dict[dataset_name]
                    del self.data_partitioner_ref_cnt_dict[dataset_name]
            if job_id in self.task_finished:
                del self.task_finished[job_id]
            print(f"Worker {self.id}: recieve job {job_id} remove")
        return executor_pb2.ack(ack=True)  
    
    async def TASK_REGIST(self, request, context):
        job_id, client_id = request.job_id, request.client_id
        event = request.event
        conf = pickle.loads(request.task_meta)
        model = pickle.loads(request.task_data)
        conf["model_weight"] = model
        conf["job_id"] = job_id
        conf["client_id"] = client_id
        conf["event"] = event
        async with self.lock:
            self.task_to_do.append(conf)
        
        print(f"Worker {self.id}: recieve job {job_id} task register")
        return executor_pb2.ack(ack=True)
    
    async def PING(self, request, context):
        job_id, client_id = request.job_id, request.client_id
        event = request.event

        if event == MODEL_TEST:
            key = event
        elif event == CLIENT_TRAIN:
            key = f"{event}{client_id}"

        async with self.lock:
            if job_id in self.task_finished:
                if key in self.task_finished[job_id]:
                    result = self.task_finished[job_id][key]

                    result_msg = executor_pb2.task_result(
                            ack=True,
                            result=pickle.dumps(result),
                            data=pickle.dumps(DUMMY_RESPONSE)
                        )
                    del self.task_finished[job_id][key]

                    return result_msg
                
            result_msg = executor_pb2.task_result(
                ack=False,
                result=pickle.dumps(DUMMY_RESPONSE),
                data=pickle.dumps(DUMMY_RESPONSE)
            )
            return result_msg
    
    async def HEART_BEAT(self, request, context):
        async with self.lock:
            status_msg = executor_pb2.worker_status(task_size=len(self.task_to_do))
            return status_msg
        
    async def _train(self, client_id, partition: Data_partitioner, model: Torch_model_adapter, conf: dict)->dict:
        self._completed_steps = 0
        self._epoch_train_loss = 1e-4

        client_data = select_dataset(client_id=client_id, 
                                     partition=partition,
                                     batch_size=conf['batch_size'],
                                     args=conf,
                                     is_test=False,
                                     )

        model = model.to(device=self.device)
        model.train()

        # trained_unique_samples = min(
        #     len(client_data.dataset), conf.local_steps * conf.batch_size
        # )

        optimizer = self._get_optimizer(model, conf)
        criterion = self._get_criterion(conf)
        
        while self._completed_steps < conf['local_steps']:
            try:
                #TODO 
                self._train_step(client_data, conf, model, optimizer, criterion)
            except Exception as ex:
                print(ex)
                break
        
        state_dict = model.state_dict()
        model_param = [state_dict[p].data.cpu().numpy() for p in state_dict]
        results = {
            'model_weight': model_param,
            'moving_loss': self._epoch_train_loss, 
            'trained_size': self._completed_steps * conf['batch_size'],
        }  

        print(f"Worker {self.id}: Job {conf['job_id']} Client {client_id}: training complete===")

        self._completed_steps = 0
        self._epoch_train_loss = 1e-4

        return results
    
    async def _test(self, client_id: int, partition: Data_partitioner, model: Torch_model_adapter, conf: dict)->dict:
        test_data = select_dataset(
            client_id=client_id, 
            partition=partition, 
            batch_size=conf['test_bsz'],
            args=conf,
            is_test=True)
        criterion = self._get_criterion(conf)
        
        test_loss = 0
        correct = 0
        top_5 = 0
        test_len = 0
        model = model.to(device=self.device)
        model.eval()

        with torch.no_grad():
            for data, target in test_data:
                try:
                    data = Variable(data).to(device=self.device)
                    target = Variable(target).to(device=self.device)
                    output = model(data)
                    loss = criterion(output, target)
                    loss = loss.tolist()

                    test_loss += sum(loss)
                    acc = accuracy(output, target, topk=(1, 5))
                    correct += acc[0].item()
                    top_5 += acc[1].item()
                except Exception as ex:
                    print(ex)
                    break
                test_len += len(target)
        
        test_len = max(test_len, 1)
        test_loss /= len(test_data)

        acc = round(correct / test_len, 4)
        acc_5 = round(top_5 / test_len, 4)
        test_loss = round(test_loss, 4)

        results = {
            "test_loss": test_loss,
            "acc": acc,
            "acc_5": acc_5,
            "test_len": test_len
        }

        print(f"Worker {self.id}: Job {conf['job_id']}: testing complete, {results}===")
        return results
        
    async def execute(self):
        while True:
            try:
                async with self.lock:
                    task_conf = self.task_to_do.popleft()
                    partition = self.data_partitioner_dict[self.job_id_data_map[task_conf["job_id"]]]
                
                    event = task_conf["event"]
                    model_weight = task_conf["model_weight"]
                    client_id = task_conf["client_id"]
                    job_id = task_conf["job_id"]

                    print(f"Worker {self.id}: executing job {job_id} {event}")
                    
                    del task_conf["model_weight"]

                    if event == CLIENT_TRAIN:
                        results = await self._train(client_id=client_id,
                                    partition=partition,
                                    model=model_weight,
                                    conf=task_conf)
                        key = f"{event}{task_conf['client_id']}"
                    elif event == MODEL_TEST:
                        results = await self._test(client_id=client_id,
                                                partition=partition,
                                                model=model_weight,
                                                conf=task_conf
                                                )
                        key = event
                
                    if job_id not in self.task_finished:
                        self.task_finished[job_id] = {}
                    self.task_finished[job_id][key] = results
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                print(e)
                await asyncio.sleep(5)
    
async def run(config):
    async def server_graceful_shutdown():
        print(f"===Worker {worker.id} ending===")
        await server.stop(5)

    channel_options = [
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH)
    ]

    server = grpc.aio.server(options=channel_options)

    if len(sys.argv) != 2:
        print("Usage: python evaluation/executor/worker.py <id>")
        exit(1)

    id = int(sys.argv[1])
    worker = Worker(id, config)
    _cleanup_coroutines.append(server_graceful_shutdown())

    executor_pb2_grpc.add_WorkerServicer_to_server(worker, server)
    
    server.add_insecure_port(f"{worker.ip}:{worker.port}")
    await server.start()
    print(f"Worker {worker.id}: started, listening on {worker.ip}:{worker.port}")

    await worker.execute()

if __name__ == '__main__':
    config_file = './evaluation/evaluation_config.yml'
    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
