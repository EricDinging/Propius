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


if __name__ == "__main__":
    args = {
        'connection_timeout' : 100,

    }
    args = Namespace(**args)
    aggregator = Aggregator(args)
    aggregator.run()