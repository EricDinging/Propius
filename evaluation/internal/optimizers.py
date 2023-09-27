# Source:
# https://github.com/SymbioticLab/FedScale/blob/master/fedscale/cloud/aggregation/optimizers.py

import numpy as np
import torch
class TorchServerOptimizer:
    """This is a abstract server optimizer class
    
    Args:
        mode (string): mode of gradient aggregation policy
        args (distionary): Variable arguments for fedscale runtime config. defaults to the setup in arg_parser.py
        device (string): Runtime device type
        sample_seed (int): Random seed

    """
    def __init__(self, mode, args, device, sample_seed=233):

        self.mode = mode
        self.args = args
        self.device = device

        if mode == 'fed-yogi':
            from evaluation.internal.optimizer_lib.yogi import YoGi
            self.gradient_controller = YoGi(
                eta=args['yogi_eta'], tau=args['yogi_tau'], beta1=args['yogi_beta1'], beta2=args['yogi_beta2'])
            
    def update_round_gradient(self, last_model, current_model, target_model):
        """ update global model based on different policy
        
        Args:
            last_model (list of tensor weight): A list of global model weight in last round.
            current_model (list of tensor weight): A list of global model weight in this round.
            target_model (PyTorch or TensorFlow nn module): Aggregated model.
        
        """

        if self.mode == 'fed-yogi':
            """
            "Adaptive Federated Optimizations", 
            Sashank J. Reddi, Zachary Charles, Manzil Zaheer, Zachary Garrett, Keith Rush, Jakub Konecný, Sanjiv Kumar, H. Brendan McMahan,
            ICLR 2021.
            """
            last_model = [x.to(device=self.device) for x in last_model]
            current_model = [x.to(device=self.device) for x in current_model]

            diff_weight = self.gradient_controller.update([
                pb - pa for pa, pb in zip(last_model, current_model) 
            ])

            new_state_dict = {
                name: torch.from_numpy(np.array(last_model[idx].cpu() + diff_weight[idx].cpu(), dtype=np.float32)) for idx, name in enumerate(target_model.state_dict().keys())
            }
        
        elif self.mode == 'fed-avg':
            new_state_dict = {
                name: torch.from_numpy(np.array(current_model[i].cpu(), dtype=np.float32)) for i, name in enumerate(target_model.state_dict().keys())
            }

        target_model.load_state_dict(new_state_dict)