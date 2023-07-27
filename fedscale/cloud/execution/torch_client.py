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
        optimizer = self.get_optimizer(model, conf)
        criterion = self.get_criterion(conf)
        error_type = None

        # NOTE: If one may hope to run fixed number of epochs, instead of iterations,
        # use `while self.completed_steps < conf.local_steps * len(client_data)` instead
        while self.completed_steps < conf.local_steps:
            try:
                self.train_step(client_data, conf, model, optimizer, criterion)
            except Exception as ex:
                error_type = ex
                break

        state_dicts = model.state_dict()
        #TODO analysis result



    def get_optimizer(self, model, conf):
        #TODO detection and nlp task
        optimizer = torch.optim.SGD(
            model.parameters(), lr=conf.learning_rate,
            momentim=0.9, weight_decay=5e-4
        )
        return optimizer
    
    def get_criterion(self, conf):
        criterion = None
        #TODO voice
        criterion = torch.nn.CrossEntropyLoss(reduction='none').to(device=self.device)
        return criterion
    
    def train_step(self, client_data, conf, model, optimizer, criterion):
        for data_pair in client_data:
            #TODO other task
            (data, target) = data_pair
            data = Variable(data).to(device=self.device)
            target = Variable(target).to(device=self.device)

            output = model(data)
            loss = criterion(output, target)

            loss_list = loss.tolist()
            loss = loss.mean()

            temp_loss = sum(loss_list) / float(len(loss_list))
            self.loss_squared = sum([l**2 for l in loss_list]) / float(len(loss_list))

            if self.completed_steps < len(client_data):
                if self.epoch_train_loss == 1e-4:
                    self.epoch_train_loss = temp_loss
                else:
                    self.epoch_train_loss = (1. - conf.loss_decay) * \
                        self.epoch_train_loss + \
                            conf.loss_decay * temp_loss
                    
            # ========= Define the backward loss ==============
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # ========= Weight handler ========================
            #TODO optimizer
            # self.optimizer.update_client_weight(
            #     conf, model, self.global_model if self.global_model is not None else None)

            self.completed_steps += 1

            if self.completed_steps == conf.local_steps:
                break



    
        
