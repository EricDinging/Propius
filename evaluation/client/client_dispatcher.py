import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import matplotlib.pyplot as plt
import time
import random
import asyncio
import yaml
import logging
import logging.handlers
import pickle
import os
from evaluation.client.client import *

async def run(config):
    public_constraint_name = config['job_public_constraint']
    private_constraint_name = config['job_private_constraint']
    ideal_client = config['ideal_client']

    client_comm_dict = None
    with open(config['client_comm_path'], 'rb') as client_file:
        client_comm_dict = pickle.load(client_file)

    client_spec_dict = None
    with open(config['client_spec_path'], 'rb') as client_file:
        client_spec_dict = pickle.load(client_file)

    client_size_dict = None
    with open(config['client_size_path'], 'rb') as client_file:
        client_size_dict = pickle.load(client_file)

    client_avail_dict = None
    with open(config['client_avail_path'], 'rb') as client_file:
        client_avail_dict = pickle.load(client_file)
    client_num = config['client_num']

    eval_start_time = time.time()

    task_list = []
    total_client_num = len(client_avail_dict)

    await asyncio.sleep(10)
    try:
        for i in range(client_num):
            client_idx = random.randint(0, total_client_num - 1)
            # client_idx = i
            public_specs = {
                    name: client_spec_dict[client_idx % len(client_spec_dict)][name]
                    for name in public_constraint_name}
            private_specs = {
                    "dataset_size": client_size_dict[client_idx % len(client_size_dict)]}
            
            if ideal_client:
                active_time = [0]
                inactive_time = [3600 * 24 * 7]
            else:
                active_time = [ x/config['speedup_factor'] for x in client_avail_dict[client_idx + 1]['active']]
                inactive_time = [ x/config['speedup_factor'] for x in client_avail_dict[client_idx + 1]['inactive']] 
            client_config = {
                    "id": client_idx,
                    "public_specifications": public_specs,
                    "private_specifications": private_specs,
                    "load_balancer_ip": config['load_balancer_ip'],
                    "load_balancer_port": config['load_balancer_port'],
                    "computation_speed": client_spec_dict[client_idx % len(client_spec_dict)]['speed'],
                    "communication_speed": client_comm_dict[client_idx % len(client_comm_dict) + 1]['communication'],
                    "eval_start_time": eval_start_time,
                    "active": active_time,
                    "inactive": inactive_time,
                    "dispatcher_use_docker": config["dispatcher_use_docker"],
                    "speedup_factor": config["speedup_factor"],
                    "is_FA": config["is_FA"],
                    "verbose": False
                }
            task = asyncio.create_task(Client(client_config).run())
            task_list.append(task)

        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        for task in task_list:
            task.cancel()

    finally:
        await asyncio.gather(*task_list, return_exceptions=True)

if __name__ == '__main__':
    client_num = int(sys.argv[1])
    dispatcher_id = int(sys.argv[2])

    log_file = f'./evaluation/monitor/client/dispatcher_{dispatcher_id}.log'

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    setup_file = './evaluation/evaluation_config.yml'

    random.seed(42)

    with open(setup_file, "r") as yamlfile:
        try:
            config = yaml.load(yamlfile, Loader=yaml.FullLoader)
            config["client_num"] = client_num
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            custom_print(e, ERROR)
        finally:
            pass