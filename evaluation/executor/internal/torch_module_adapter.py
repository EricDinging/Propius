from typing import List
import numpy as np
import torch

class Torch_model_adapter:
    def __init__(self, model: torch.nn.Module):
        self.model = model

    def set_weights(self, weights: List[np.ndarray]):
        new_state_dict = {
            name: torch.from_numpy(np.asarray(weights[i], dtype=np.float32)) for i, name in enumerate(self.model.state_dict().keys())
        }

        self.model.load_state_dict(new_state_dict)

    def get_weights(self)-> List[np.ndarray]:
        return [params.data.clone() for params in self.model.state_dict().values()]
    
    def get_model(self):
        return self.model