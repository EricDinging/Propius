import csv
from random import Random
import numpy as np
from torch.utils.data import DataLoader
from collections import defaultdict

class Partition:
    def __init__(self, data, index):
        def __init__(self, data, index):
            self.data = data
            self.index = index

        def __len__(self):
            return len(self.index)
        
        def __getitem__(self, index):
            data_idx = self.index[index]
            return self.data[data_idx]
        
class Data_partitioner:
    def __init__(self, data, args, num_of_labels=0, seed=1, is_test=False):
        self.partitions = []

        self.data = data
        self.labels = self.data.targets
        self.args = args
        self.is_test = is_test
        np.random.seed(seed)

        self.data_len = len(self.data)
        self.num_of_labels = num_of_labels
        self.client_label_cnt = defaultdict(set)

    def get_num_of_labels(self):
        return self.num_of_labels
    
    def get_data_len(self):
        return self.data_len
    
    def get_client_len(self):
        return len(self.partitions)
    
    def get_client_label_len(self):
        return [len(self.client_label_cnt[i]) for i in range(self.get_client_len)]
    
    def trace_partition(self, data_map_file):
        """Read data mapping from data_map_file. Format: <client_id, sample_name, sample_category, category_id>"""
        print(f"Partitioning data by profile {data_map_file}...")
        client_id_maps = {}
        