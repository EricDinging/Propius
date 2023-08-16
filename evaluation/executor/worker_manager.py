from evaluation.executor.task_pool import *
from evaluation.executor.internal.torch_module_adapter import *
from evaluation.executor.internal.dataset_handler import *
from evaluation.executor.internal.test_helper import *

import math
import torch
from torch.autograd import Variable
from torch.nn import CTCLoss
import numpy as np
import random
from typing import List

import asyncio
import sys
import pickle

class Worker_manager:
    def __init__(self, config):
        """Init worker class

        Args:
            config:
        """
  
        self.job_id_model_adapter_map = {}
        self.job_id_agg_weight_map = {}
        self.job_id_agg_cnt = {}
        # self.num_worker = config['num_worker']
        self.lock = asyncio.Lock()

        self._setup_seed()

        self.config = config

    def _setup_seed(self, seed=1):
        torch.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        random.seed(seed)


    async def remove_job(self, job_id: int):
        async with self.lock:
            if job_id in self.job_id_model_adapter_map:
                del self.job_id_model_adapter_map[job_id]
                del self.job_id_agg_weight_map[job_id]
                del self.job_id_agg_cnt[job_id]


    async def init_job(self, job_id: int, dataset_name: str, model_name: str)->float:
        async with self.lock:
            

            model = None
            if model_name == "resnet18":
                from fedscale.utils.models.specialized.resnet_speech import resnet18
                model = resnet18(
                    num_classes=out_put_class[dataset_name],
                    in_channels=1
                )
            elif model_name == "mobilenet":
                from fedscale.utils.models.specialized.resnet_speech import \
                mobilenet_v2
                model = mobilenet_v2(num_classes=out_put_class[dataset_name])

            model_adapter = Torch_model_adapter(model)
                # model_adapter.set_weights(model_weights)
            model_size = sys.getsizeof(pickle.dumps(model_adapter)) / 1024.0 * 8.  # kbits
            self.job_id_model_adapter_map[job_id] = model_adapter
            self.job_id_agg_weight_map[job_id] = []
            self.job_id_agg_cnt[job_id] = 0
            return model_size

    async def execute(self, event: str, job_id: int, client_id: int, args: dict)->dict:
        async with self.lock:
            if event == CLIENT_TRAIN:
                model_param, results = self._train(client_id=client_id, 
                            partition=self.data_partitioner_dict[self.job_id_data_map[job_id]],
                            model=self.job_id_model_adapter_map[job_id].get_model(),
                            conf=args)
                
                self.job_id_agg_cnt[job_id] += 1

                agg_weight = self.job_id_agg_weight_map[job_id]
                if self.job_id_agg_cnt[job_id] == 1:
                    agg_weight = model_param
                else:
                    agg_weight = [weight + model_param[i] for i, weight in enumerate(agg_weight)]
                self.job_id_agg_weight_map[job_id] = agg_weight

                results = {CLIENT_TRAIN+str(client_id): results}

            elif event == AGGREGATE:
                agg_weight = self.job_id_agg_weight_map[job_id]
                agg_weight = [np.divide(weight, self.job_id_agg_cnt[job_id]) for weight in agg_weight]

                self.job_id_model_adapter_map[job_id].set_weights(copy.deepcopy(agg_weight))
                results = {
                    "agg_number": self.job_id_agg_cnt[job_id]
                }
                self.job_id_agg_cnt[job_id] = 0

                results = {AGGREGATE: results}

            elif event == MODEL_TEST:
                results = self._test(
                    client_id=client_id,
                    partition=self.test_data_partition_dict[self.job_id_data_map[job_id]],
                    model=self.job_id_model_adapter_map[job_id].get_model(),
                    conf=args,
                )

                results = {
                    MODEL_TEST: results
                }
            
            return results
            

