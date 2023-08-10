from evaluation.executor.task_pool import *
from evaluation.executor.internal import torch_module_adapter

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
        self.training_set_dict = {}
        self.testing_set_dict = {}

        # self.num_worker = config['num_worker']
        self.cur_job = -1

        self._setup_seed()

        #TODO GPU
        self.device = torch.device('cpu')

    def _setup_seed(self, seed=1):
        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)

    
        
    def remove_job(self):
        pass

    def init_job(self):
        pass

    def execute(self, event: str, client_id: int)->dict:
        pass