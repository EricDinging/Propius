from evaluation.executor.task_pool import *
from evaluation.executor.internal import torch_module_adapter
from evaluation.executor.internal.dataset_handler import *

import math
import torch
from torch.autograd import Variable
from torch.nn import CTCLoss
import numpy as np
import random
from typing import List

import asyncio

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

        #TODO GPU
        self.device = torch.device('cpu')

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
            model.parameters(), lr=conf.learning_rate,
            momentum=0.9, weight_decay=5e-4
        )
        return optimizer
    
    def _get_criterion(self, conf):
        criterion = None
        criterion = torch.nn.CrossEntropyLoss(reduction='none').to(device=self.device)
        return criterion
    
    def _train_step(self, client_data: DataLoader, conf, model, optimizer, criterion):
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
                    self._epoch_train_loss = (1. - conf.loss_decay) * \
                        self._epoch_train_loss + conf.loss_decay * temp_loss
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            self._completed_steps += 1

            if self._completed_steps == conf.local_steps:
                break

    def _train(self, client_id, partition: Data_partitioner, model, conf)->tuple[dict, dict]:
        self._completed_steps = 0
        self._epoch_train_loss = 1e-4

        client_data = select_dataset(client_id=client_id, 
                                     partition=partition,
                                     batch_size=conf.batch_size,
                                     args=conf,
                                     is_test=False,
                                     )
        print(f"Worker: Client {client_id}: === Starting to train ===")
        model = model.to(device=self.device)
        model.train()

        trained_unique_samples = min(
            len(client_data.dataset), conf.local_steps * conf.batch_size
        )

        optimizer = self._get_optimizer(model, conf)
        criterion = self._get_criterion(conf)
        
        while self._completed_steps < conf.local_steps:
            try:
                #TODO 
                self._train_step(client_data, conf, model, optimizer, criterion)
            except Exception as ex:
                print(ex)
                break
        
        state_dict = model.state_dict()
        model_param = {p: state_dict[p].data.cpu().numpy() for p in state_dict}
        results = {'moving_loss': self._epoch_train_loss, 
                  'trained_size': self._completed_steps * conf.batch_size,
        }       

        print(f"Worker: Client {client_id}: training complete, {results}===")

        return (model_param, results)

    async def remove_job(self, job_id: int):
        async with self.lock:
            dataset_name = self.job_id_data_map[job_id]
            del self.job_id_data_map[job_id]
            del self.job_id_model_adapter_map[job_id]
            del self.job_id_agg_weight_map[job_id]
            del self.job_id_agg_cnt[job_id]
            self.data_partitioner_ref_cnt_dict[dataset_name] -= 1
            if self.data_partitioner_dict[dataset_name] <= 0:
                del self.data_partitioner_dict[dataset_name]
                del self.test_data_partition_dict[dataset_name]
                del self.data_partitioner_ref_cnt_dict[dataset_name]

    async def init_job(self, job_id: int, dataset_name: str, model_name: str):
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

                    self.data_partitioner_dict[dataset_name] = Data_partitioner(data=train_dataset, num_of_labels=out_put_class[dataset_name])
                    self.data_partitioner_dict[dataset_name].partition_data_helper(0, data_map_file=self.config['femnist_data_map_file'])
                    
                    self.test_data_partition_dict[dataset_name] = Data_partitioner(data=test_dataset, num_of_labels=out_put_class[dataset_name])
                    self.test_data_partition_dict[dataset_name].partition_data_helper(0, data_map_file=self.config['femnist_test_data_map_file'])

                self.data_partitioner_ref_cnt_dict[dataset_name] = 0

            self.data_partitioner_ref_cnt_dict[dataset_name] += 1

            model = None
            if model_name == "resnet_18":
                from fedscale.utils.models.specialized.resnet_speech import resnet18
                model = resnet18(
                    num_classes=out_put_class[dataset_name],
                    in_channels=1
                )
                model_adapter = torch_module_adapter(model)
                # model_adapter.set_weights(model_weights)
            self.job_id_model_adapter_map[job_id] = model_adapter
            self.job_id_agg_weight_map[job_id] = model_adapter.get_weights()
            self.job_id_agg_cnt[job_id] = 0

    async def execute(self, event: str, job_id: int, client_id: int, args)->dict:
        async with self.lock:
            if event == CLIENT_TRAIN:
                model_param, results = self._train(client_id=client_id, 
                            partition=self.data_partitioner_dict[self.job_id_data_map[job_id]],
                            model=self.job_id_model_adapter_map[job_id],
                            conf=args)
                self.job_id_agg_cnt[job_id] += 1
                self.job_id_agg_weight_map[job_id] = None #TODO aggregate

            elif event == AGGREGATE:
                self.job_id_model_adapter_map[job_id] = self.job_id_agg_weight_map[job_id] #TODO
                self.job_id_agg_cnt[job_id] = 0

            elif event == MODEL_TEST:
                #TODO
                pass
            
            

