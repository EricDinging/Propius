import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import matplotlib.pyplot as plt
import time
import random
import asyncio
import yaml
import logging
from evaluation.client.client import *

async def run(gconfig):
    # clients = []
    num = int(gconfig['client_num'])
    total_time = int(gconfig['total_running_second'])
    is_uniform = gconfig['client_is_uniform']
    public_constraint_name = gconfig['job_public_constraint']
    private_constraint_name = gconfig['job_private_constraint']
    start_time_list = [0] * total_time

    if not is_uniform:
        for i in range(num):
            time = random.normalvariate(total_time / 2, total_time / 4)
            while time < 0 or time >= total_time:
                time = random.normalvariate(total_time / 2, total_time / 4)
            start_time_list[int(time)] += 1
    else:
        for i in range(num):
            time = random.randint(0, total_time - 1)
            start_time_list[int(time)] += 1

    for i in range(total_time):
        for _ in range(start_time_list[i]):
            bench_mark = max(20, min(random.normalvariate(60, 20), 100))

            public_specs = [
                int(bench_mark + max(-bench_mark, min(random.normalvariate(0, 5), 100 - bench_mark)))
                for _ in range(len(public_constraint_name))]

            private_specs = [
                int(bench_mark + max(-bench_mark, min(random.normalvariate(0, 5), 100 - bench_mark)))
                for _ in range(len(private_constraint_name))]

            client_config = {
                "public_specifications": public_specs,
                "private_specifications": private_specs,
                "load_balancer_ip": gconfig['load_balancer_ip'],
                "load_balancer_port": gconfig['load_balancer_port']
            }
            asyncio.ensure_future(
                Client(client_config).run())

        await asyncio.sleep(1)

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()

    global_setup_file = './evaluation/evaluation_config.yml'

    random.seed(42)

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)

            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(str(e))
        finally:
            pass