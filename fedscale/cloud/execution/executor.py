# -*- coding: utf-8 -*-
import collections
import pickle
import random
import time

import numpy as np
import torch

import fedscale.cloud.channels.job_api_pb2 as job_api_pb2
from fedscale.cloud.channels.channel_context import ClientConnections
#TODO tensorfloew client
from fedscale.cloud.execution.torch_client import TorchClient
from fedscale.cloud.execution.data_processor import collate #TODO voice collate fn
#TODO RL client
from fedscale.cloud.fllibs import *
from fedscale.dataloaders.divide_data import DataPartitioner, select_dataset

class Executor(object):
    """Abstract class for FedScale executor.

    Args:
        args (dictionary): Variable arguments for fedscale runtime config. defaults to the setup in arg_parser.py

    """

    def __init__(self, args):
        #TODO logger

        self.model_adapter = self.get_client_trainer(args).get_model_adapter(init_model())

        self.args = args
        self.num_executors = args.num_executors
        # ======== env information ========
        self.this_rank = args.this_rank
        self.executor_id = str(self.this_rank)

        # ======== model and data ========
        self.training_sets = self.test_dataset = None

        # ======== channels ========
        self.aggregator_communicator = ClientConnections(
            args.ps_ip, args.ps_port)
        
        # ======== runtime information ========
        self.collate_fn = None
        self.round = 0
        self.start_run_time = time.time()
        self.recieved_stop_request = False
        self.event_queue = collections.deque()

        #TODO wandb
        self.wandb = None
        super(Executor, self).__init__()

    def get_client_trainer(self, conf):
        """
        Returns a framework-specific client that handles training and evaluation.
        :param conf: job config
        :return: framework-specific client instance
        """
        #TODO tensorflow
        #TODO RLclient
        return TorchClient(conf)
    
    def setup_env(self):
        """Set up experiments environment
        """
        #TODO logging
        self.setup_seed(seed=1)

    def init_data(self):
        """Return the training and testing dataset

        Returns:
            Tuple of DataPartitioner class: The partioned dataset class for training and testing

        """
        train_dataset, test_dataset = init_dataset()
        #TODO various tasks
        # load data partitionxr (entire_train_data)
        #TODO logging
        training_sets = DataPartitioner(
            data=train_dataset, args=self.args, numOfClass=self.args.num_class)
        training_sets.partition_data_helper(
            num_clients=self.args.num_participants, data_map_file=self.args.data_map_file)
        
        testing_sets = DataPartitioner(
            data=test_dataset, args=self.args, numOfClass=self.args.num_class, isTest=True)
        testing_sets.partition_data_helper(num_clients=self.num_executors)

        #TODO logging

        return training_sets, testing_sets

    def setup_communication(self):
        """Set up grpc connection
        """
        self.init_control_communication()
        self.init_data_communication()

    def init_control_communication(self):
        """Create communication channel between coordinator and executor.
        This channel serves control messages.
        """
        self.aggregator_communicator.connect_to_server()

    def init_data_communication(self):
        """In charge of jumbo data traffics (e.g., fetch training result)
        """
        pass

    def event_monitor(self):
        pass
        #TODO
    
    def run(self):
        """Start running the executor by setting up execution and communication environment, and monitoring the grpc message.
        """
        self.setup_env()
        self.training_sets, self.testing_sets = self.init_data()
        self.setup_communication()
        self.event_monitor()

    

if __name__ == "__main__":
    executor = Executor(parser.args)
    executor.run()