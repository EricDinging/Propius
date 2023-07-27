import logging
import math
import time

import torch
from torch.autograd import Variable

from torch.nn import CTCLoss
from fedscale.cloud.execution.client_base import ClientBase
from fedscale.cloud.execution.optimizers import ClientOptimizer
from fedscale.cloud.internal.torch_model_adapter import TorchModelAdapter
