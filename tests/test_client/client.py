import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import random
import yaml
from test_job.parameter_server.channels import parameter_server_pb2_grpc
from test_job.parameter_server.channels import parameter_server_pb2
from propius.client.propius_client_aio import *

class Client:
    def __init__(self, client_config: dict):
        self.id = -1
        self.task_id = -1
        self.propius_client_stub = Propius_client_aio(client_config=client_config, verbose=True)
        self.job_channel = None
        self.job_stub = None
        self.workload = 0
        self.result = 0
        self.client_plotter = None
        self.ttl = 3

    async def _connect_to_ps(self, job_ip: str, job_port: int):
        self.job_channel = grpc.aio.insecure_channel(f"{job_ip}:{job_port}")
        self.job_stub = parameter_server_pb2_grpc.Parameter_serverStub(self.job_channel)
        print(
            f"Client {self.id}: connecting to parameter server on {job_ip}:{job_port}")

    async def request(self) -> bool:
        client_id_msg = propius_pb2.client_id(id=self.id)
        plan = await self.job_stub.CLIENT_REQUEST(client_id_msg)
        ack = plan.ack
        if not ack:
            print(f"Client {self.id}: not recieving ack from parameter server")
            return False
        self.workload = plan.workload
        print(f"Client {self.id}: request job plan, workload {self.workload}")
        return True

    async def execute(self):
        print(f"Client {self.id}: executing task {self.task_id}")
        metric_product = 1
        # TODO execute time calculation
        # for m in self.public_specifications:
        #     metric_product *= m
        # extra_time_scale = (1 - metric_product / 1000000)
        # exec_time = self.workload * (1 + 0.1 * extra_time_scale * math.exp(random.gauss(0, 1)))
        exec_time = self.workload
        await asyncio.sleep(exec_time)

        self.result = random.normalvariate(0, 1)
        print(
            f"Client {self.id}: task {self.task_id} done! result: {self.result}")

    async def report(self):
        print(f"Client {self.id}: Report to job")

        client_report_msg = parameter_server_pb2.client_report(
            client_id=self.id, result=self.result)
        await self.job_stub.CLIENT_REPORT(client_report_msg)

        print(f"Client {self.id}: result reported")

    async def cleanup_routines(self):
        try:
            await self.propius_client_stub.close()
            await self.job_channel.close()
        except Exception:
            pass

    async def run(self, client_plotter=None):
        self.client_plotter = client_plotter
        if client_plotter:
            await client_plotter.client_start()
        
        try:
            await self.propius_client_stub.connect()

            self.id, status, self.task_id, job_ip, job_port = await self.propius_client_stub.auto_assign(10)
        
            await self.propius_client_stub.close()
            
            if not status:
                return

            # Execute task
            await self._connect_to_ps(job_ip, job_port)

            job_ack = None
            while True:
                job_ack = await self.request()
                if job_ack:
                    break
                if self.ttl == 0:
                    raise ValueError(
                        f"cannot make request to parameter server")
                await asyncio.sleep(5)
                self.ttl -= 1

            await self.execute()
            await self.report()
            if client_plotter:
                await client_plotter.client_finish('success')
            print(
                f"Client {self.id}: task {self.task_id} executed, shutting down===")
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Client {self.id}: {e}")
            if self.client_plotter:
                await self.client_plotter.client_finish('drop')
        finally:
            await self.cleanup_routines()


if __name__ == '__main__':
    config_file = './test_client/test_profile.yml'
    with open(config_file, 'r') as config:
        config = yaml.load(config, Loader=yaml.FullLoader)
        client = Client(config)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.run(None))
        loop.close()
