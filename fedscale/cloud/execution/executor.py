import pickle
import random
import time

import numpy as np
import torch

import fedscale.cloud.channels.job_api_pb2 as job_api_pb2
from fedscale.cloud.channels.channel_context import ClientConnections
from fedscale.cloud.execution.torch_client import TorchClient