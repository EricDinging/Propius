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