# From FedScale/fedscale/cloud/internal

from typing import List
import numpy as np
import torch
import copy
from evaluation.executor.internal.optimizers import TorchServerOptimizer

class Torch_model_adapter:
    def __init__(self, model: torch.nn.Module, optimizer: TorchServerOptimizer):
        """
        Initializes a TorchModelAdapter.
        :param model: the PyTorch model to adapt
        :param optimizer: the optimizer to apply weights, when specified.
        """
        self.model = model
        self.optimizer = optimizer

    def set_weights(self, weights: List[np.ndarray]):
        """
        Set the model's weights to the numpy weights array.
        :param weights: numpy weights array
        """
        current_grad_weights = [param.data.clone() for param in self.model.state_dict().values()]

        weights_origin = copy.deepcopy(weights)
        new_weights = [torch.tensor(x) for x in weights_origin]
        self.optimizer.update_round_gradient(current_grad_weights,
                                            new_weights,
                                            self.model)


    def get_weights(self)-> List[np.ndarray]:
        return [params.data.clone() for params in self.model.state_dict().values()]
    
    def get_model(self):
        return self.model