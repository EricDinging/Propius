import ruamel.yaml

propius_config_file = './propius/global_config.yml'
compose_redis_file = './compose_redis.yml'
propius_use_docker = True

propius_compose_file = './compose_propius.yml'

client_manager_num = 1
client_manager_port_start = 50003
client_db_port_start = 6380

evaluation_config_file = './evaluation/evaluation_config.yml'
evaluation_use_docker = False
do_compute = False
is_FA = False
use_cuda = False
speedup_factor = 2.5

sched_alg = 'fifo'

profile_folder = './evaluation/job/profile_policy_test'
job_trace = './evaluation/job/profile_policy_test/job_trace.txt'
total_job = 5
ideal_client = True
client_num = 50


def set(propius_data, redis_data, config_data, propius_compose_data):
    propius_data["client_manager"] = [
    {"ip": "localhost",
     "port": client_manager_port_start + i,
     "client_db_port": client_db_port_start + i}
     for i in range(client_manager_num)
    ]

    propius_data["use_docker"] = propius_use_docker
    propius_data["verbose"] = True
    propius_data["sched_alg"] = sched_alg

    for i in range(100):
        if f'client_db_{i}' in redis_data['services']:
            del redis_data['services'][f'client_db_{i}']
        if f'client_db_{i}' in propius_compose_data['services']:
            del propius_compose_data['services'][f'client_db_{i}']
            del propius_compose_data['services'][f'client_manager_{i}']

    for i in range(client_manager_num):
        new_client_db_service = {
            f"client_db_{i}": {
                'build': {
                'context': '.',
                'dockerfile': './propius/database/Dockerfile'
                },
                'command': [f'{client_db_port_start + i}'],
                'ports': [f'{client_db_port_start + i}:{client_db_port_start + i}'],
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
                    './propius/client_manager:/propius/client_manager',
                    './propius/global_config.yml:/propius/global_config.yml',
                    './propius/monitor:/propius/monitor',
                    './propius/channels:/propius/channels',
                    './propius/util:/propius/util',
                    './propius/database:/propius/database'
                ],
                'depends_on': [
                    'job_db',
                    f'client_db_{i}',
                    'scheduler',
                ],
                'command': ['0'],
                'environment': ['TZ=America/Detroit']
            }
        }
        redis_data['services'].update(new_client_db_service)
        propius_compose_data['services'].update(new_client_manger_service)
        propius_compose_data['services'].update(new_client_db_service)

    propius_compose_data['services']['load_balancer']['depends_on'] = [
        f'client_manager_{i}' for i in range(client_manager_num)
    ]
    propius_compose_data['services']['scheduler']['depends_on'] = [
        f'client_db_{i}' for i in range(client_manager_num)
    ]

    config_data["use_docker"] = evaluation_use_docker
    config_data["do_compute"] = do_compute
    config_data["is_FA"] = is_FA
    config_data["use_cuda"] = use_cuda
    config_data["speedup_factor"] = speedup_factor
    config_data["sched_alg"] = sched_alg
    config_data["job_trace"] = job_trace
    config_data["profile_folder"] = profile_folder
    config_data["ideal_client"] = ideal_client
    config_data["total_job"] = total_job
    config_data["client_num"] = client_num

yaml = ruamel.yaml.YAML()
with open(compose_redis_file, 'r') as redis_file:
    redis_data = yaml.load(redis_file)

with open(evaluation_config_file, 'r') as evaluation_config_yaml_file:
    config_data = yaml.load(evaluation_config_yaml_file)

with open(propius_config_file, 'r') as propius_config_yaml_file:
    propius_data = yaml.load(propius_config_yaml_file)

with open(propius_compose_file, 'r') as propius_compose_yaml_file:
    propius_compose_data = yaml.load(propius_compose_yaml_file)

set(propius_data, redis_data, config_data, propius_compose_data)


with open(propius_config_file, 'w') as propius_config_yaml_file:
    yaml.dump(propius_data, propius_config_yaml_file) 

with open(evaluation_config_file, 'w') as evaluation_config_yaml_file:
    yaml.dump(config_data, evaluation_config_yaml_file)

with open(compose_redis_file, 'w') as redis_file:
    yaml.dump(redis_data, redis_file)

with open(propius_compose_file, 'w') as propius_compose_yaml_file:
    yaml.dump(propius_compose_data, propius_compose_yaml_file)