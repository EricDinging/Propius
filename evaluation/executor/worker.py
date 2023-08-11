from evaluation.executor.task_pool import *
from evaluation.executor.internal import torch_module_adapter
from evaluation.executor.internal.dataset_handler import *

import math
import torch
from torch.autograd import Variable
from torch.nn import CTCLoss
import numpy as np
import random

class Worker:
    def __init__(self, config):
        """Init worker class

        Args:
            config:
                use_cuda
                cuda_device
        """
        self.model_adapter_dict = {}

        # self.num_worker = config['num_worker']
        self.cur_job = -1

        self._setup_seed()

        #TODO GPU
        self.device = torch.device('cpu')

        self._completed_steps = 0
        self.epoch_train_loss = 1e-4

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
                if self.epoch_train_loss == 1e-4:
                    self.epoch_train_loss = temp_loss
                else:
                    self.epoch_train_loss = (1. - conf.loss_decay) * \
                        self.epoch_train_loss + conf.loss_decay * temp_loss
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            self._completed_steps += 1

            if self._completed_steps == conf.local_steps:
                break

    def _train(self, client_id, partition: Data_partitioner, model, conf)->tuple[dict, dict]:
        self._completed_steps = 0
        self.epoch_train_loss = 1e-4

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
        results = {'moving_loss': self.epoch_train_loss, 
                  'trained_size': self._completed_steps * conf.batch_size,
        }       

        print(f"Worker: Client {client_id}: training complete, {results}===")

        return (model_param, results)


        
    def remove_job(self):
        pass

    def init_job(self):
        pass

    def execute(self, event: str, client_id: int)->dict:
        pass