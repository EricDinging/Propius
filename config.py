import ruamel.yaml
import math
import random
import os

PROPIUS_SYS = 0
PROPIUS_POLICY = 1
PROPIUS_EVAL = 2

option = PROPIUS_SYS

propius_config_file = './propius/global_config.yml'
compose_file = ''
evaluation_config_file = './evaluation/evaluation_config.yml'

propius_use_docker = True

client_manager_num = 2
client_manager_port_start = 50003
client_db_port_start = 6380
ideal_client = False
client_num = 8000

speedup_factor = 3
sched_alg = 'fifo'

profile_folder = './evaluation/job/profile_mobilenet'
job_trace = './evaluation/job/trace/job_trace_10.txt'
total_job = 10


if option == PROPIUS_SYS:
    compose_file = './compose_propius.yml'
    do_compute = False
else:
    evaluation_use_docker = True
    client_per_container = 1000
    job_per_container = 1
    if option == PROPIUS_POLICY:
        compose_file = './compose_eval.yml'
        do_compute = False
    elif option == PROPIUS_EVAL:
        compose_file = './compose_eval_gpu.yml'
        do_compute = True
        use_cuda = True

def cleanup():
    for i in range(100):
        if f'worker_{i}' in compose_data['services']:
            del compose_data['services'][f'worker_{i}']
        if f'jobs_{i}' in compose_data['services']:
            del compose_data['services'][f'jobs_{i}']
        if f'clients_{i}' in compose_data['services']:
            del compose_data['services'][f'clients_{i}']
        if f'client_db_{i}' in compose_data['services']:
            del compose_data['services'][f'client_db_{i}']
        if f'client_manager_{i}' in compose_data['services']:
            del compose_data['services'][f'client_manager_{i}']

def config_scheduler():
    compose_data['services']['scheduler']['depends_on'] = [
        f'client_db_{i}' for i in range(client_manager_num)
    ]

def config_job_manager():
    if option == PROPIUS_SYS:
        compose_data['services']['job_manager']['ports'] = ['50001:50001']
    else:
        if 'ports' in compose_data['services']['job_manager']:
            del compose_data['services']['job_manager']['ports']

def config_load_balancer():
    if option == PROPIUS_SYS:
        compose_data['services']['load_balancer']['ports'] = ['50002:50002']
    else:
        if 'ports' in compose_data['services']['load_balancer']:
            del compose_data['services']['load_balancer']['ports']
        
    compose_data['services']['load_balancer']['depends_on'] = [
        f'client_manager_{i}' for i in range(client_manager_num)
    ]

def config_client_manager():
    for i in range(client_manager_num):
        new_client_db_service = {
            f"client_db_{i}": {
                'build': {
                'context': '.',
                'dockerfile': './propius/database/Dockerfile'
                },
                'command': [f'{client_db_port_start + i}'],
                'environment': ['TZ=America/Detroit']
            }
        }

        new_client_manger_service = {
            f"client_manager_{i}": {
                'build': {
                'context': '.',
                'dockerfile': './propius/client_manager/Dockerfile'
                },
                'volumes': [
                    './propius:/propius'
                ],
                'depends_on': [
                    'job_db',
                    f'client_db_{i}',
                    'scheduler',
                ],
                'command': [f'{i}'],
                'environment': ['TZ=America/Detroit'],
                'stop_signal': 'SIGINT'
            }
        }
        compose_data['services'].update(new_client_manger_service)
        compose_data['services'].update(new_client_db_service)

yaml = ruamel.yaml.YAML()

with open(evaluation_config_file, 'r') as evaluation_config_yaml_file:
    config_data = yaml.load(evaluation_config_yaml_file)

with open(propius_config_file, 'r') as propius_config_yaml_file:
    propius_data = yaml.load(propius_config_yaml_file)

with open(compose_file, 'r') as compose_yaml_file:
    compose_data = yaml.load(compose_yaml_file)




with open(propius_config_file, 'w') as propius_config_yaml_file:
    yaml.dump(propius_data, propius_config_yaml_file) 

with open(evaluation_config_file, 'w') as evaluation_config_yaml_file:
    yaml.dump(config_data, evaluation_config_yaml_file)

with open(compose_file, 'w') as compose_yaml_file:
    yaml.dump(compose_data, compose_yaml_file)

