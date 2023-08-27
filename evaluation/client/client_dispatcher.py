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
from evaluation.client.client import *

async def run(config):
    # clients = []
    # num = int(config['client_num'])
    # total_time = int(config['total_running_second'])
    public_constraint_name = config['job_public_constraint']
    # private_constraint_name = config['job_private_constraint']
    # start_time_list = [0] * total_time

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
    selected_client_avail = {i: client_avail_dict[i+1] for i in range(client_num)}

    eval_start_time = time.time()
    
    # if not is_uniform:
    #     for i in range(num):
    #         time = random.normalvariate(total_time / 2, total_time / 4)
    #         while time < 0 or time >= total_time:
    #             time = random.normalvariate(total_time / 2, total_time / 4)
    #         start_time_list[int(time)] += 1
    # else:
    #     for i in range(num):
    #         time = random.randint(0, total_time - 1)
    #         start_time_list[int(time)] += 1

    task_list = []

    await asyncio.sleep(10)
    try:

        for client_idx in range(client_num):
            public_specs = {
                    name: client_spec_dict[client_idx % len(client_spec_dict)][name]
                    for name in public_constraint_name}
            private_specs = {
                    "dataset_size": client_size_dict[client_idx % len(client_size_dict)]}
            
            client_config = {
                    "id": client_idx,
                    "public_specifications": public_specs,
                    "private_specifications": private_specs,
                    "load_balancer_ip": config['load_balancer_ip'],
                    "load_balancer_port": config['load_balancer_port'],
                    "computation_speed": client_spec_dict[client_idx % len(client_spec_dict)]['speed'],
                    "communication_speed": client_comm_dict[client_idx % len(client_comm_dict) + 1]['communication'],
                    "eval_start_time": eval_start_time,
                    "active": selected_client_avail[client_idx]['active'],
                    "inactive": selected_client_avail[client_idx]['inactive'],
                    "use_docker": config["use_docker"],
                }
            task = asyncio.create_task(Client(client_config).run())
            task_list.append(task)

        while True:
            await asyncio.sleep(5)
    except KeyboardInterrupt:
        for task in task_list:
            task.cancel()

    finally:
        await asyncio.gather(*task_list, return_exceptions=True)

if __name__ == '__main__':
    log_file = './evaluation/client/app.log'
    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    global_setup_file = './evaluation/evaluation_config.yml'

    random.seed(42)

    with open(global_setup_file, "r") as gyamlfile:
        try:
            config = yaml.load(gyamlfile, Loader=yaml.FullLoader)

            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config))
        except KeyboardInterrupt:
            pass
        # except Exception as e:
            # logger.error(str(e))

        finally:
            pass