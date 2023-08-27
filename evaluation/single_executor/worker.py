from evaluation.single_executor.task_pool import *
from evaluation.single_executor.internal.torch_module_adapter import *
from evaluation.single_executor.internal.dataset_handler import *
from evaluation.single_executor.internal.test_helper import *

import math
import torch
from torch.autograd import Variable
from torch.nn import CTCLoss
import numpy as np
import random
from typing import List

import asyncio
import sys
import pickle

class Worker:
    def __init__(self, config):
        """Init worker class

        Args:
            config:
                use_cuda
                cuda_device
        """
        self.job_id_data_map = {}
        self.data_partitioner_dict = {}
        self.test_data_partition_dict = {}
        self.data_partitioner_ref_cnt_dict = {}

        self.job_id_model_adapter_map = {}
        self.job_id_agg_weight_map = {}
        self.job_id_agg_cnt = {}
        # self.num_worker = config['num_worker']
        self.lock = asyncio.Lock()

        self._setup_seed()

        #TODO use other device
        if config["use_cuda"]:
            self.device = torch.device(config['cuda_device'])
        else:
            self.device = torch.device("cpu")
       
        custom_print(f"Worker: use {self.device}", INFO)

        self._completed_steps = 0
        self._epoch_train_loss = 1e-4

        self.config = config

    def _setup_seed(self, seed=1):
        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)

    def _get_optimizer(self, model, conf):
        optimizer = torch.optim.SGD(
            model.parameters(), lr=conf['learning_rate'],
            momentum=0.9, weight_decay=5e-4
        )
        return optimizer
    
    def _get_criterion(self, conf):
        criterion = None
        criterion = torch.nn.CrossEntropyLoss(reduction='none').to(device=self.device)
        return criterion
    
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

            custom_print(f"Worker: step {self._completed_steps} completed")
            self._completed_steps += 1

            if self._completed_steps == conf['local_steps']:
                break

    def _train(self, client_id, partition: Data_partitioner, model: Torch_model_adapter, conf: dict)->tuple:
        self._completed_steps = 0
        self._epoch_train_loss = 1e-4

        client_data = select_dataset(client_id=client_id, 
                                     partition=partition,
                                     batch_size=conf['batch_size'],
                                     args=conf,
                                     is_test=False,
                                     )
        custom_print(f"Worker: Client {client_id}: === Starting to train ===", INFO)
        model = model.to(device=self.device)
        model.train()

        # trained_unique_samples = min(
        #     len(client_data.dataset), conf.local_steps * conf.batch_size
        # )

        optimizer = self._get_optimizer(model, conf)
        criterion = self._get_criterion(conf)
        
        while self._completed_steps < conf['local_steps']:
            try:
                self._train_step(client_data, conf, model, optimizer, criterion)
            except Exception as ex:
                custom_print(ex, ERROR)
                break
        
        state_dict = model.state_dict()
        model_param = [state_dict[p].data.cpu().numpy() for p in state_dict]
        results = {'moving_loss': self._epoch_train_loss, 
                  'trained_size': self._completed_steps * conf['batch_size'],
        }       

        custom_print(f"Worker: Client {client_id}: training complete, {results}===", INFO)

        return (model_param, results)
    
    def _test(self, client_id: int, partition: Data_partitioner, model: Torch_model_adapter, conf: dict)->dict:
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
        return results

    async def remove_job(self, job_id: int):
        async with self.lock:
            if job_id in self.job_id_data_map:
                dataset_name = self.job_id_data_map[job_id]
                del self.job_id_data_map[job_id]
                del self.job_id_model_adapter_map[job_id]
                del self.job_id_agg_weight_map[job_id]
                del self.job_id_agg_cnt[job_id]
                self.data_partitioner_ref_cnt_dict[dataset_name] -= 1
                if self.data_partitioner_ref_cnt_dict[dataset_name] <= 0:
                    del self.data_partitioner_dict[dataset_name]
                    del self.test_data_partition_dict[dataset_name]
                    del self.data_partitioner_ref_cnt_dict[dataset_name]

    async def init_job(self, job_id: int, dataset_name: str, model_name: str)->float:
        async with self.lock:
            self.job_id_data_map[job_id] = dataset_name

            if dataset_name not in self.data_partitioner_dict:
                #TODO init data partitioner
                #TODO test data partitioner
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

            model = None
            if model_name == "resnet18":
                from fedscale.utils.models.specialized.resnet_speech import resnet18
                model = resnet18(
                    num_classes=out_put_class[dataset_name],
                    in_channels=1
                )
            elif model_name == "mobilenet":
                from fedscale.utils.models.specialized.resnet_speech import \
                mobilenet_v2
                model = mobilenet_v2(num_classes=out_put_class[dataset_name])

            model_adapter = Torch_model_adapter(model)
                # model_adapter.set_weights(model_weights)
            model_size = sys.getsizeof(pickle.dumps(model_adapter)) / 1024.0 * 8.  # kbits
            self.job_id_model_adapter_map[job_id] = model_adapter
            self.job_id_agg_weight_map[job_id] = []
            self.job_id_agg_cnt[job_id] = 0
            return model_size

    async def execute(self, event: str, job_id: int, client_id: int, args: dict)->dict:
        async with self.lock:
            if event == CLIENT_TRAIN:
                model_param, results = self._train(client_id=client_id, 
                            partition=self.data_partitioner_dict[self.job_id_data_map[job_id]],
                            model=self.job_id_model_adapter_map[job_id].get_model(),
                            conf=args)
                
                self.job_id_agg_cnt[job_id] += 1

                agg_weight = self.job_id_agg_weight_map[job_id]
                if self.job_id_agg_cnt[job_id] == 1:
                    agg_weight = model_param
                else:
                    agg_weight = [weight + model_param[i] for i, weight in enumerate(agg_weight)]
                self.job_id_agg_weight_map[job_id] = agg_weight

            elif event == AGGREGATE:
                agg_weight = self.job_id_agg_weight_map[job_id]
                agg_weight = [np.divide(weight, self.job_id_agg_cnt[job_id]) for weight in agg_weight]

                self.job_id_model_adapter_map[job_id].set_weights(copy.deepcopy(agg_weight))
                results = {
                    "agg_number": self.job_id_agg_cnt[job_id]
                }
                self.job_id_agg_cnt[job_id] = 0

            elif event == MODEL_TEST:
                results = {
                    "test_loss": 0,
                    "acc": 0,
                    "acc_5": 0,
                    "test_len": 0
                }

                for i in range(self.config['client_test_num']):
                    custom_print(f"Worker: starting client {i} test", INFO)
                    temp_results = self._test(
                        client_id=i,
                        partition=self.test_data_partition_dict[self.job_id_data_map[job_id]],
                        model=self.job_id_model_adapter_map[job_id].get_model(),
                        conf=args,
                    )
                    for key in results.keys():
                        results[key] += temp_results[key]
            
                for key in results.keys():
                    if key != "test_len":
                        results[key] /= results["test_len"]

            return results

