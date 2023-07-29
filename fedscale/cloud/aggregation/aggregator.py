# -*- coding: utf-8 -*-
import collections
import copy
import math
import os
import pickle
import random
import threading
import time
from concurrent import futures

import grpc
import numpy as np
import torch
#TODO import wandb

import fedscale.cloud.channels.job_api_pb2_grpc as job_api_pb2_grpc
from fedscale.cloud.channels import job_api_pb2
from fedscale.cloud.aggregation.optimizers import TorchServerOptimizer
#TODO job manager
from fedscale.cloud.internal.torch_model_adapter import TorchModelAdapter
#TODO resource manager
from fedscale.cloud.fllibs import *

from argparse import Namespace

MAX_MESSAGE_LENGTH = 1 * 1024 * 1024 * 1024  # 1GB

class Aggregator(job_api_pb2_grpc.JobServiceServicer):
    """This centralized aggregator collects training/testing feedbacks from executors

    Args:
        args (dictionary): Variable arguments for fedscale runtime config. defaults to the setup in arg_parser.py

    """

    def __init__(self, args):
        self.args = args
        #TODO deployment
        self.experiment_mode = 'deployment'
        self.device = 'cpu'

        # ======== env information ========
        self.this_rank = 0
        #TODO virtual clock
        #TODO resource manager/client manager

        # ======== model and data ========
        self.model_wrapper = None
        self.model_in_update = 0
        self.update_lock = threading.Lock()
        # all weights including bias/#_batch_tracked (e.g., state_dict)
        self.model_weigths = None
        #TODO model saving

        # ======== channels ========
        self.connection_timeout = self.args.connection_timeout
        self.executors = None
        self.grpc_server = None

        # ======== Event Queue =======
        self.individual_client_events = {}  # Unicast
        self.sever_events_queue = collections.deque()
        self.broadcast_events_queue = collections.deque()  # Broadcast

        # ======== runtime information ========
        self.tasks_round = 0
        self.num_of_clients = 0

        self.sampled_participants = []

        self.round_stragglers = []
        self.model_update_size = 0.

        self.collate_fn = None
        self.round = 0

        self.start_run_time = time.time()
        self.client_conf = {}
        
        self.stats_util_accumulator = []
        self.loss_accumulator = []
        self.client_training_results = []

        # number of registered executors
        self.registered_executor_info = set()
        self.test_result_accumulator = []
        #TODO testing history
        #TODO log
        #TODO wandb
        #TODO init task context

    def setup_env(self):
        """Set up experiments environment and server optimizer
        """
        self.setup_seed(seed=1)

    def setup_seed(self, seed=1):
        """Set global random seed for better reproducibility

        Args:
            seed (int): random seed

        """
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)
        torch.backends.cudnn.deterministic = True

    def init_control_communication(self):
        """Create communication channel between coordinator and executor.
        This channel serves control messages.
        """
        #TODO logging
        #TODO self executors

        # initiate a server process
        self.grpc_server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=20),
            options=[
                ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH),
            ],
        )

        job_api_pb2_grpc.add_JobServiceServicer_to_server(
            self, self.grpc_server)
        port = f"{self.args.ps_ip}:{self.args.ps_port}"
        #TODO logging
        self.grpc_server.add_insecure_port(port)
        self.grpc_server.start()

    def init_model(self):
        """Initialize the model"""
        #TODO tensorflow
        if self.args.engine == commons.PYTORCH:
            if args.model == "resnet18":
                from fedscale.utils.models.specialized.resnet_speech import resnet18

                model = resnet18(num_classes=outputClass[args.data_set], in_channels=1)
                self.model_wrapper = TorchModelAdapter(model, 
                                                       optimizer=TorchServerOptimizer(
                    self.args.gradient_policy, self.args, self.device))
                self.model_weigths = self.model_wrapper.get_weights()

    def event_monitor(self):
        """Activate event handler according to the received new message
        """
        while True:
            # Broadcast events to clients
            if len(self.broadcast_events_queue) > 0:
                current_event = self.broadcast_events_queue.popleft()

                if current_event in (commons.UPDATE_MODEL, commons.MODEL_TEST):
                    self.dispatch_client_events(current_event)

                elif current_event == commons.START_ROUND:
                    self.dispatch_client_events(commons.CLIENT_TRAIN)

                elif current_event == commons.SHUT_DOWN:
                    self.dispatch_client_events(commons.SHUT_DOWN)
                    #TODO edit logic for deployment
                    break
            
            # Handle events queued on the aggregator
            elif len(self.server_events_queue) > 0:
                client_id, current_event, _, data = self.sever_events_queue.popleft()

                if current_event == commons.UPLOAD_MODEL:
                    self.client_completion_handler(
                        self.deserialize_response(data))
                    if len(self.stats_util_accumulator) == self.tasks_round:
                        self.round_completion_handler()
                
                elif current_event == commons.MODEL_TEST:
                    self.testing_completion_handler(
                        client_id, self.deserialize_response(data))
                    
                else:
                    #TODO logging
                    pass
            
            else:
                # execute every 100 ms
                time.sleep(0.1)




    def run(self):
        """Start running the aggregator server by setting up execution
        and communication environment, and monitoring the grpc message.
        """
        self.setup_env()
        #TODO load client profile
        print(f"Job server: init control communication")
        self.init_control_communication()
        #TODO init data communication

        self.init_model()
        self.model_update_size = sys.getsizeof(
            pickle.dumps(self.model_wrapper)) / 1024.0 * 8.
        
        #TODO self.event_monitor()
        self.stop()
    
    def stop(self):
        """Stop the aggregator
        """
        #TODO: logging
        #TODO: wandb
        time.sleep(5)

if __name__ == "__main__":
    args = {
        'connection_timeout' : 100,
        'ps_ip' : 'localhost',
        'ps_port' : 61000,
        'engine' : 'pytorch',
        'model' : 'resnet18',
        'dataset' : 'femnist',
        'gradient_policy' : 'fedavg',
    }
    args = Namespace(**args)
    aggregator = Aggregator(args)
    aggregator.run()