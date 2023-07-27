import logging
import math
import time

import torch
from torch.autograd import Variable
from torch.nn import CTCLoss
from fedscale.cloud.execution.client_base import ClientBase
#from fedscale.cloud.execution.optimizers import ClientOptimizer
from fedscale.cloud.internal.torch_model_adapter import TorchModelAdapter

class TorchClient(ClientBase):
    """Implements a PyTorch-based client for training and evaluation."""

    def __init__(self, args):
        """
        Initializes a torch client.
        :param args: Job args
        """
        self.args = args
        #self.optimizer = ClientOptimizer()
        self.device = args.cuda_device if args.use_cuda else torch.device(
            'cpu')
        
        self.epoch_train_loss = 1e-4
        self.completed_steps = 0
        self.loss_squared = 0
    
    def train(self, client_data, model, conf):
        """
        Perform a training task.
        :param client_data: client training dataset
        :param model: the framework-specific model
        :param conf: job config
        :return: training results
        """
        client_id = conf.client_id
        logging.info(f"Start to train (CLIENT: {client_id}) ...")
        tokenizer = conf.tokenizer

        model = model.to(device=self.device)
        model.train()

        trained_unique_samples = min(
            len(client_data.dataset), conf.local_setps * conf.batch_size
        )
        self.global_model = None

        #TODO fedprox
        #TODO optimizer


    def get_optimizer(self, model, conf):
        #TODO detection and nlp task
        optimizer = torch.optim.SGD(
            model.parameters(), lr=conf.learning_rate,
            momentim=0.9, weight_decay=5e-4
        )
        return optimizer

    
        
