import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import grpc
import pickle
import sys
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc
from evaluation.commons import *
from evaluation.internal.torch_module_adapter import *
from evaluation.internal.dataset_handler import *
from evaluation.internal.test_helper import *
from collections import deque
from typing import List
from evaluation.internal.dataloaders.utils_data import get_data_transform

import torch
from torch.autograd import Variable
import numpy as np
import random
import os
import logging
import logging.handlers
import math
import pickle


_cleanup_coroutines = []

class Worker(executor_pb2_grpc.WorkerServicer):
    def __init__(self, id: int, config: dict, logger: My_logger):
        self.id = id
        self.logger = logger
        if id >= len(config["worker"]):
            raise ValueError("Invalid worker ID")
        
        self.ip = config["worker"][id]["ip"] if not config["use_docker"] else "0.0.0.0"
        self.port = config["worker"][id]["port"]
        device = config["worker"][id]["device"] if config["use_cuda"] else "cpu"
        self.device = torch.device(device)
        self.logger.print(f"Worker {self.id}: Use {self.device}", INFO)

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

        self.job_id_model_adapter_map = {}

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
    
    def _train_step(self, client_data: DataLoader, conf: dict, model, optimizer, criterion):
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
        model = pickle.loads(request.model_weight)
        model_adapter = Torch_model_adapter(model,
                                            optimizer=TorchServerOptimizer(
                                            mode=job_meta["gradient_policy"], 
                                            args=job_meta, 
                                            device=self.device)
                                            )
        dataset_name = job_meta["dataset"]

        self.job_id_data_map[job_id] = dataset_name

        if dataset_name not in self.data_partitioner_dict:
            if dataset_name == "femnist":
                from evaluation.internal.dataloaders.femnist import FEMNIST

                train_transform, test_transform = get_data_transform("mnist")
                train_dataset = FEMNIST(
                    self.config['data_dir'],
                    dataset='train',
                    transform=train_transform
                )
                test_dataset = FEMNIST(
                    self.config['data_dir'],
                    dataset='test',
                    transform=test_transform
                )
                
                train_partitioner = Data_partitioner(data=train_dataset, num_of_labels=out_put_class[dataset_name])
                train_partitioner.partition_data_helper(0, data_map_file=self.config['data_map_file'])
                self.data_partitioner_dict[dataset_name] = train_partitioner
                
                test_partitioner = Data_partitioner(data=test_dataset, num_of_labels=out_put_class[dataset_name])
                test_partitioner.partition_data_helper(0, data_map_file=self.config['test_data_map_file'])
                self.test_data_partition_dict[dataset_name] = test_partitioner
            
            elif dataset_name == "openImg":
                from evaluation.internal.dataloaders.openimage import OpenImage
                train_transform, test_transform = get_data_transform("openImg")
                train_dataset = OpenImage(
                    self.config['data_dir'], split='train', download=False, transform=train_transform)
                test_dataset = OpenImage(
                    self.config["data_dir"], split='val', download=False, transform=test_transform)
                
                train_partitioner = Data_partitioner(data=train_dataset, num_of_labels=out_put_class[dataset_name])
                train_partitioner.partition_data_helper(0, data_map_file=self.config['data_map_file'])
                self.data_partitioner_dict[dataset_name] = train_partitioner
                
                test_partitioner = Data_partitioner(data=test_dataset, num_of_labels=out_put_class[dataset_name])
                test_partitioner.partition_data_helper(self.config["client_test_num"])
                self.test_data_partition_dict[dataset_name] = test_partitioner

            self.data_partitioner_ref_cnt_dict[dataset_name] = 0
        
        self.data_partitioner_ref_cnt_dict[dataset_name] += 1
        self.job_id_model_adapter_map[job_id] = model_adapter
        self.task_finished[job_id] = {}
        self.logger.print(f"Worker {self.id}: recieve job {job_id} init", INFO)

        return executor_pb2.ack(ack=True)
    
    async def REMOVE(self, request, context):
        job_id = request.job_id
        if job_id in self.job_id_model_adapter_map:
            del self.job_id_model_adapter_map[job_id]
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
        self.logger.print(f"Worker {self.id}: recieve job {job_id} remove", INFO)
        return executor_pb2.ack(ack=True)  
    
    async def UPDATE(self, request, context):
        job_id = request.job_id
        weight = pickle.loads(request.job_data)
        self.logger.print(f"Update job {job_id} weight", INFO)
        try:
            if job_id in self.job_id_model_adapter_map:
                self.job_id_model_adapter_map[job_id].set_weights(weight)
                ack = True
            else:
                ack = False
        except Exception as e:
            self.logger.print(e, ERROR)
            ack = False
        return executor_pb2.ack(ack=ack)
        
    async def TASK_REGIST(self, request, context):
        client_id_list = pickle.loads(request.client_id_list)
        conf = pickle.loads(request.task_meta)
        conf["job_id"] = request.job_id
        conf["client_id_list"] = client_id_list
        conf["event"] = request.event
        conf["round"] = request.round
        conf["task_id"] = request.task_id
        self.task_to_do.append(conf)
        
        # self.logger.print(f"Worker {self.id}: recieve job {job_id} {event}{client_id}", INFO)
        return executor_pb2.ack(ack=True)
    
    async def PING(self, request, context):
        job_id = request.job_id
        task_id = request.task_id

        if job_id in self.task_finished:
            if task_id in self.task_finished[job_id]:
                result = self.task_finished[job_id][task_id]

                result_msg = executor_pb2.worker_task_result(
                        ack=True,
                        result_data=pickle.dumps(result),
                    )
                del self.task_finished[job_id][task_id]

                return result_msg
                
        result_msg = executor_pb2.worker_task_result(
            ack=False,
            result_data=pickle.dumps(DUMMY_RESPONSE),
        )
        self.logger.print(f"Worker {self.id}: job {job_id} {task_id} retrieval fail", WARNING)
        return result_msg
    
    async def HEART_BEAT(self, request, context):
        status_msg = executor_pb2.worker_status(task_size=len(self.task_to_do))
        self.logger.print(f"Worker {self.id}: queueing length {len(self.task_to_do)}", INFO)
        return status_msg
        
    async def _train(self, client_id, partition: Data_partitioner, model, conf: dict)->dict:
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
        optimizer = self._get_optimizer(model, conf)
        criterion = self._get_criterion(conf)
        
        while self._completed_steps < conf['local_steps']:
            try:
                self._train_step(client_data, conf, model, optimizer, criterion)
            except Exception as ex:
                self.logger.print(ex, ERROR)
                break
        
        state_dict = model.state_dict()
        model_param = [state_dict[p].data.cpu().numpy() for p in state_dict]
        results = {
            'model_weight': model_param,
            'moving_loss': self._epoch_train_loss, 
            'trained_size': self._completed_steps * conf['batch_size'],
        }  

        self.logger.print(f"Worker {self.id}: Job {conf['job_id']} Client {client_id}: training complete===", INFO)

        self._completed_steps = 0
        self._epoch_train_loss = 1e-4

        return results
    
    async def _test(self, client_id: int, partition: Data_partitioner, model, conf: dict)->dict:
        test_data = select_dataset(
            client_id=client_id, 
            partition=partition, 
            batch_size=conf['test_bsz'],
            args=conf,
            is_test=True)
        criterion = self._get_criterion(conf)
        model = model.to(device=self.device)
        test_loss = 0
        correct = 0
        top_5 = 0
        test_len = 0
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
                    self.logger.print(ex, ERROR)
                    break
                test_len += len(target)
        
        test_len = max(test_len, 1)
        test_loss /= len(test_data)

        if math.isnan(test_loss):
            test_loss = 0

        acc = round(correct / test_len, 4)
        acc_5 = round(top_5 / test_len, 4)
        test_loss = round(test_loss, 4)

        results = {
            "test_loss": test_loss,
            "acc": acc,
            "acc_5": acc_5,
            "test_len": test_len
        }

        self.logger.print(f"Worker {self.id}: Job {conf['job_id']}: testing complete, {results}===", INFO)
        return results
        
    async def execute(self):
        while True:
            try:
                if len(self.task_to_do) == 0:
                    await asyncio.sleep(1)
                    continue
                task_conf = self.task_to_do.popleft()
                partition = self.data_partitioner_dict[self.job_id_data_map[task_conf["job_id"]]]
            
                event = task_conf["event"]
                client_id_list = task_conf["client_id_list"]
                job_id = task_conf["job_id"]
                model = self.job_id_model_adapter_map[job_id].get_model()
                round = task_conf["round"]
                task_id = task_conf["task_id"]

                self.logger.print(f"Worker {self.id}: executing job {job_id}-{round} {event}, Client {client_id_list}", INFO)
                if event == CLIENT_TRAIN:
                    agg_results = {
                        "cnt": 0,
                        "model_weight": None,
                        "moving_loss": 0,
                        "trained_size": 0, 
                    }
                    
                    for client_id in client_id_list:
                        results = await self._train(client_id=client_id,
                                    partition=partition,
                                    model=model,
                                    conf=task_conf)
                        agg_results["cnt"] += 1
                        model_weight = results["model_weight"]
                        if not agg_results["model_weight"]:
                            agg_results["model_weight"] = model_weight
                        else:
                            agg_results["model_weight"] = [weight + model_weight[i] 
                                                           for i, weight in enumerate(agg_results["model_weight"])]
                        agg_results["moving_loss"] += results["moving_loss"]
                        agg_results["trained_size"] += results["trained_size"]

                elif event == MODEL_TEST:
                    agg_results = {
                        "test_loss": 0,
                        "acc": 0,
                        "acc_5": 0,
                        "test_len": 0,
                        "cnt": 0,
                    }
                    for client_id in client_id_list:
                        results = await self._test(client_id=client_id,
                                                partition=partition,
                                                model=model,
                                                conf=task_conf
                                                )
                        agg_results["cnt"] += 1
                        for key, value in results.items():
                            agg_results[key] += value

                self.task_finished[job_id][task_id] = agg_results
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                self.logger.print(e, ERROR)
                await asyncio.sleep(1)
    
async def run(config, logger, id):
    async def server_graceful_shutdown():
        logger.print(f"===Worker {worker.id} ending===", WARNING)
        await server.stop(5)

    channel_options = [
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH)
    ]

    server = grpc.aio.server(options=channel_options)

    worker = Worker(id, config, logger)
    _cleanup_coroutines.append(server_graceful_shutdown())

    executor_pb2_grpc.add_WorkerServicer_to_server(worker, server)
    
    server.add_insecure_port(f"{worker.ip}:{worker.port}")
    await server.start()
    logger.print(f"Worker {worker.id}: started, listening on {worker.ip}:{worker.port}", INFO)

    await worker.execute()

if __name__ == '__main__':
    config_file = './evaluation/evaluation_config.yml'
    
    if len(sys.argv) != 2:
        print("Usage: python evaluation/executor/worker.py <id>")
        exit(1)

    id = int(sys.argv[1])

    log_file = f'./evaluation/monitor/executor/wk_{id}.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = My_logger(log_file=log_file, verbose=False, use_logging=True)
    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config, logger, id))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
