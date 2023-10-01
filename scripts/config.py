import ruamel.yaml
import math
import random
import os
import numpy as np

compose_file = './compose_eval_gpu.yml'
evaluation_config_file = './evaluation/evaluation_config.yml'
propius_config_file = './propius/global_config.yml'

profile_folder = './evaluation/job/profile_benchmark'
job_trace = './evaluation/job/trace/job_trace_10.txt'
total_job = 10

worker_num_list = [4, 4, 0, 0]
worker_num = sum(worker_num_list)

allocate_list = worker_num_list
avg_job_interval = 1800
job_per_container = 2
allow_exceed_total_round = True

ideal_client = False
client_per_container = 2000
client_num = 6000
sched_alg = 'fifo'
speedup_factor = 3

# dataset = "openImg"
dataset = "femnist"

def get_gpu_idx():
    for i, _ in enumerate(allocate_list):
        if allocate_list[i] > 0:
            allocate_list[i] -= 1
            return i

# Load the existing compose YAML file
yaml = ruamel.yaml.YAML()
with open(compose_file, 'r') as yaml_file:
    compose_data = yaml.load(yaml_file)

# Load the existing evaluation config YAML file
with open(evaluation_config_file, 'r') as evaluation_config_yaml_file:
    config_data = yaml.load(evaluation_config_yaml_file)

with open(propius_config_file, 'r') as propius_config_yaml_file:
    propius_data = yaml.load(propius_config_yaml_file) 

config_data['worker'] = []
starting_port = 49998

# remove old container configuration
for i in range(100):
    if f'worker_{i}' in compose_data['services']:
        del compose_data['services'][f'worker_{i}']
    if f'jobs_{i}' in compose_data['services']:
        del compose_data['services'][f'jobs_{i}']
    if f'clients_{i}' in compose_data['services']:
        del compose_data['services'][f'clients_{i}']

for i in range(worker_num):
    new_service = {
        f'worker_{i}': {
            'build': {
                'context': '.',
                'dockerfile': './evaluation/executor/Dockerfile_worker_gpu',
                'args': {
                    'WORKER_IMAGE': 'nvidia/cuda:11.6.2-devel-ubuntu20.04'
                }
            },
            'volumes': [
                './evaluation/executor:/evaluation/executor',
                './evaluation/evaluation_config.yml:/evaluation/evaluation_config.yml',
                './datasets:/datasets',
                './evaluation/monitor:/evaluation/monitor',
                './evaluation/internal:/evaluation/internal',
            ],
            'stop_signal': 'SIGINT',
            'command': [f'{i}'],
            'deploy': {
                'resources': {
                    'reservations': {
                        'devices':[{
                                'driver': 'nvidia',
                                'count': len(worker_num_list),
                                'capabilities': ['gpu'],
                        }]
                    }
                }
            },
            'environment': ['TZ=America/Detroit']
        }
    }

    compose_data['services'].update(new_service)

    config_data['worker'].append({
        'ip': 'localhost',
        'port': starting_port - i,
        'device': get_gpu_idx()
    })

compose_data['services']['executor']['depends_on'] = [
    f"worker_{i}" for i in range(worker_num)
]

# Config job container

for i in range(math.ceil(total_job / job_per_container)):
    start_row = i * job_per_container
    end_row = min(total_job, start_row + job_per_container)

    new_job_container = {
        f'jobs_{i}': {
            'build': {
                'context': '.',
                'dockerfile': './evaluation/job/Dockerfile'
            },
            'volumes': [
                './evaluation/job:/evaluation/job',
                './evaluation/evaluation_config.yml:/evaluation/evaluation_config.yml',
                './evaluation/monitor:/evaluation/monitor',
            ],
            'stop_signal': 'SIGINT',
            'depends_on': [
                'executor',
                'job_manager'
            ],
            'command': [
                f'{start_row}',
                f'{end_row}',
                f'{i}'
            ],
            'environment': ['TZ=America/Detroit']
        }
    }
    
    compose_data['services'].update(new_job_container)

# Config client container
config_data['client_num'] = client_num
for i in range(math.ceil(client_num / client_per_container)):
    num = min(client_per_container, client_num - i * client_per_container)

    new_client_container = {
        f'clients_{i}': {
            'build': {
                'context': '.',
                'dockerfile': './evaluation/client/Dockerfile',
            },
            'volumes': [
                './evaluation/client:/evaluation/client',
                './evaluation/evaluation_config.yml:/evaluation/evaluation_config.yml',
                './datasets/device_info:/datasets/device_info',
                './evaluation/monitor:/evaluation/monitor'
            ],
            'stop_signal': 'SIGINT',
            'depends_on': [
                'load_balancer'
            ],
            'environment': ['TZ=America/Detroit'],
            'command': [
                f'{num}',
                f'{i}'
            ],

        }
    }
    compose_data['services'].update(new_client_container)

# sched_alg
propius_data['sched_alg'] = sched_alg
config_data['sched_alg'] = sched_alg


random.seed(1)
config_data["total_job"] = total_job
# generate txt with format: time in minute, profile num, job_id
time_intervals = np.random.exponential(
    scale=avg_job_interval, size=total_job - 1)

file_path = job_trace
job_id_list= list(range(total_job))
random.shuffle(job_id_list)
if not os.path.exists(file_path):
    with open(file_path, "w") as file:
        file.write(f'0 {job_id_list[0]}\n')
        for idx, itv in enumerate(time_intervals):
            file.write(f'{int(itv)} {job_id_list[idx+1]}\n')

config_data['job_trace'] = job_trace
config_data['profile_folder'] = profile_folder
config_data['ideal_client'] = ideal_client
config_data['speedup_factor'] = speedup_factor
    
if dataset == 'femnist':
    config_data['data_dir'] = "./datasets/femnist"
    config_data['data_map_file'] = './datasets/femnist/client_data_mapping/train.csv'
    config_data['test_data_map_file'] = './datasets/femnist/client_data_mapping/test.csv'

elif dataset == 'openImg':
    #TODO
    config_data['data_dir'] = './datasets/openImg'
    config_data['data_map_file'] = './datasets/openImg/client_data_mapping/train.csv'

propius_data["allow_exceed_total_round"] = allow_exceed_total_round
# Write the updated YAML back to the file

with open(propius_config_file, 'w') as propius_config_yaml_file:
    yaml.dump(propius_data, propius_config_yaml_file) 

with open(compose_file, 'w') as yaml_file:
    yaml.dump(compose_data, yaml_file)

with open(evaluation_config_file, 'w') as evaluation_config_yaml_file:
    yaml.dump(config_data, evaluation_config_yaml_file)