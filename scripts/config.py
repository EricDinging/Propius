import ruamel.yaml

compose_file = './compose_eval_gpu.yml'
evaluation_config_file = './evaluation/evaluation_config.yml'

worker_num_list = [4, 4, 0, 0]
worker_num = sum(worker_num_list)

allocate_list = worker_num_list
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

config_data['worker'] = []
starting_port = 49998

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

# Write the updated YAML back to the file
with open(compose_file, 'w') as yaml_file:
    yaml.dump(compose_data, yaml_file)

with open(evaluation_config_file, 'w') as evaluation_config_yaml_file:
    yaml.dump(config_data, evaluation_config_yaml_file)