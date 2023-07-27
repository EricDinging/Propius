import sys
[sys.path.append(i) for i in ['.', '..', '...']]
from src.client.client import *
import logging
import yaml
import asyncio
import random
import time
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

class Client_plotter:
    def __init__(self, total_time:int):
        self.lock = asyncio.Lock()
        self.timestamp = [0]
        self.time_num_list = [0]
        self.time_start_num_list = [0 for _ in range(total_time)]

        self.start_time = int(time.time())

        self.total_client_num = 0
        self.total_client_success_num = 0
        self.total_client_drop_num = 0
    
    async def client_start(self):
        async with self.lock:
            runtime = int(time.time()) - self.start_time
            self.timestamp.append(runtime)
            self.timestamp.append(self.timestamp[-1])
            self.time_num_list.append(self.time_num_list[-1])
            self.time_num_list.append(self.time_num_list[-1] + 1)

            if runtime < len(self.time_start_num_list):
                self.time_start_num_list[runtime] += 1
            
            self.total_client_num += 1
    
    async def client_finish(self, type):
        async with self.lock:
            self.timestamp.append(int(time.time()) - self.start_time)
            self.timestamp.append(self.timestamp[-1])
            self.time_num_list.append(self.time_num_list[-1])
            self.time_num_list.append(self.time_num_list[-1] - 1)

            if type == 'success':
                self.total_client_success_num += 1
            else:
                self.total_client_drop_num += 1

    def report(self):
        rate = -1
        if self.total_client_num != 0:
            rate = self.total_client_success_num / self.total_client_num
        return self.total_client_num, self.total_client_success_num, rate, self.total_client_drop_num
    
    def plot(self):
        plt.plot(self.timestamp, self.time_num_list, label='Online')
        plt.plot(self.time_start_num_list, label="start")
        plt.title('Client trace')
        plt.ylabel('Number of clients')
        plt.xlabel('Time (sec)')

async def run(gconfig, client_plotter):
    # clients = []
    num = int(gconfig['client_num'])
    ip = gconfig['client_manager_ip']
    port = int(gconfig['client_manager_port'])
    total_time = int(gconfig['total_running_second']) + 60
    is_uniform = int(gconfig['client_is_uniform']) == 1
    public_constraint_name = gconfig['job_public_constraint']
    private_constraint_name = gconfig['job_private_constraint']
    start_time_list = [0] * total_time

    if not is_uniform:
        for i in range(num):
            time = random.normalvariate(total_time/2, total_time/4)
            while time < 0 or time >= total_time:
                time = random.normalvariate(total_time/2, total_time/4)
            start_time_list[int(time)] += 1
    else:
        start_time_list = [int(num / total_time)] * total_time

    id = 0
    for i in range(total_time):
        for _ in range(start_time_list[i]):
            bench_mark = max(20, min(random.normalvariate(60, 20), 100))
            
            public_constraints = tuple([
                int(bench_mark + max(-bench_mark, min(random.normalvariate(0, 5), 100-bench_mark)))
                for _ in range(len(public_constraint_name))]
            )
            
            private_constraints = tuple([
                int(bench_mark + max(-bench_mark, min(random.normalvariate(0, 5), 100-bench_mark)))
                for _ in range(len(private_constraint_name))]   
            )
            
            asyncio.ensure_future(
                Client(id, public_constraints, private_constraints, ip, port).run(client_plotter))

            id += 1
        await asyncio.sleep(1)

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()

    global_setup_file = './global_config.yml'
    
    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            client_plotter = Client_plotter(int(gconfig['total_running_second']) + 60)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(gconfig, client_plotter))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(str(e))
        finally:
            if client_plotter.total_client_num > 0:
                fig = plt.gcf()
                client_plotter.plot()
                plt.legend(loc='upper left')
                plt.show()
                fig.savefig(f'./fig/CLIENT-{int(time.time())}')
                total, success_num, rate, drop_num = client_plotter.report()
                str = f"Total client: {total}, success num: {success_num}, usage rate: {rate:.3f}, drop num: {drop_num}"
                with open(f'./log/CLIENT-{int(time.time())}.txt', 'w') as file:
                    file.write(str)
                    file.write("\n")