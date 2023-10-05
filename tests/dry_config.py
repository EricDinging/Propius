import ruamel.yaml
import os

propius_config_file = './propius/global_config.yml'
compose_redis_file = './compose_redis.yml'

client_manager_num = 1
client_manager_port_start = 50003
client_db_port_start = 6380

propius_use_docker = False

def set_client_manager_db(propius_data, redis_data, 
                          propius_use_docker, client_manager_num,
                          client_manager_port_start,
                          client_db_port_start):
    propius_data["client_manager"] = [
    {"ip": "localhost",
     "port": client_manager_port_start + i,
     "client_db_port": client_db_port_start + i}
     for i in range(client_manager_num)
    ]

    propius_data["use_docker"] = propius_use_docker
    propius_data["verbose"] = True

    for i in range(100):
        if f'client_db_{i}' in redis_data['services']:
            del redis_data['services'][f'client_db_{i}']

    for i in range(client_manager_num):
        new_service = {
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
        redis_data['services'].update(new_service)

yaml = ruamel.yaml.YAML()
with open(compose_redis_file, 'r') as redis_file:
    redis_data = yaml.load(redis_file)

with open(propius_config_file, 'r') as propius_config_yaml_file:
    propius_data = yaml.load(propius_config_yaml_file)

set_client_manager_db(propius_data, redis_data, 
                        propius_use_docker, client_manager_num,
                        client_manager_port_start,
                        client_db_port_start)

with open(propius_config_file, 'w') as propius_config_yaml_file:
    yaml.dump(propius_data, propius_config_yaml_file) 

with open(compose_redis_file, 'w') as redis_file:
    yaml.dump(redis_data, redis_file)