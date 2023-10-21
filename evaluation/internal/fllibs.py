from evaluation.internal.dataloaders.utils_data import get_data_transform
from evaluation.internal.dataset_handler import *
from evaluation.commons import *

def init_data_set(dataset_name: str, config: dict, data_partitioner_dict: dict, test_data_partition_dict: dict):
    if dataset_name == "femnist":
        from evaluation.internal.dataloaders.femnist import FEMNIST

        train_transform, test_transform = get_data_transform("mnist")
        train_dataset = FEMNIST(
            config['data_dir'],
            dataset='train',
            transform=train_transform
        )
        test_dataset = FEMNIST(
            config['data_dir'],
            dataset='test',
            transform=test_transform
        )
        
        train_partitioner = Data_partitioner(data=train_dataset, num_of_labels=out_put_class[dataset_name])
        train_partitioner.partition_data_helper(0, data_map_file=config['data_map_file'])
        data_partitioner_dict[dataset_name] = train_partitioner
        
        test_partitioner = Data_partitioner(data=test_dataset, num_of_labels=out_put_class[dataset_name])
        test_partitioner.partition_data_helper(0, data_map_file=config['test_data_map_file'])
        test_data_partition_dict[dataset_name] = test_partitioner
    
    elif dataset_name == "openImg":
        from evaluation.internal.dataloaders.openimage import OpenImage
        train_transform, test_transform = get_data_transform("openImg")
        train_dataset = OpenImage(
            config['data_dir'], split='train', download=False, transform=train_transform)
        test_dataset = OpenImage(
            config["data_dir"], split='val', download=False, transform=test_transform)
        
        train_partitioner = Data_partitioner(data=train_dataset, num_of_labels=out_put_class[dataset_name])
        train_partitioner.partition_data_helper(0, data_map_file=config['data_map_file'])
        data_partitioner_dict[dataset_name] = train_partitioner
        
        test_partitioner = Data_partitioner(data=test_dataset, num_of_labels=out_put_class[dataset_name])
        test_partitioner.partition_data_helper(config["client_test_num"])
        test_data_partition_dict[dataset_name] = test_partitioner