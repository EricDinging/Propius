import grpc
import yaml
import random
import math
import asyncio
from propius.src.channels import propius_pb2
from propius.src.channels import propius_pb2_grpc

class Client:
    def __init__(self, id:int, cpu:int, memory:int, os:int,
                 cm_ip:str, cm_port:int):
        self.id = id
        self.metrics = [cpu, memory, os]

        self.task_id = 0

        self.cm_channel = None
        self.cm_stub = None
        self._connect_cm(cm_ip, cm_port)

        self.job_channel = None
        self.job_stub = None
        self.workload = 0
        self.result = 0

    def _connect_cm(self, cm_ip:str, cm_port:int)->None:
        self.cm_channel = grpc.insecure_channel(f'{cm_ip}:{cm_port}')
        self.cm_stub = propius_pb2_grpc.Client_managerStub(self.cm_channel)
        print(f"Client {self.id}: connecting to client manager at {cm_ip}:{cm_port}")

    async def checkin(self)->propius_pb2.cm_offer:
        metric_msg = propius_pb2.metrics(cpu=self.metrics[0], memory=self.metrics[1], os=self.metrics[2])
        client_checkin_msg = propius_pb2.client_checkin(client_id=self.id, cmetrics=metric_msg)

        task_offer = self.cm_stub.CLIENT_CHECKIN(client_checkin_msg)
        print(f"Client {self.id}: recieve client manager offer: {task_offer}")
        return task_offer
    
    async def accept(self, cm_offer:propius_pb2.cm_offer)->propius_pb2.cm_ack:
        task_id = int(cm_offer.task_offer)
        self.task_id = task_id
        client_accept_msg = propius_pb2.client_accept(client_id=self.id, task_id=task_id)
        cm_ack = self.cm_stub.CLIENT_ACCEPT(client_accept_msg)
        return cm_ack
    
    async def request(self, job_ip:str, job_port:int):
        self.job_channel = grpc.insecure_channel(f"{job_ip}:{job_port}")
        self.job_stub = propius_pb2_grpc.JobStub(self.job_channel)
        client_id_msg = propius_pb2.client_id(id=self.id)
        plan = self.job_stub.CLIENT_REQUEST(client_id_msg)
        self.workload = plan.workload
        print(f"Client {self.id}: request job plan, workload {self.workload}")

    async def execute(self):
        print(f"Client {self.id}: executing task {self.task_id}")
        metric_product = 1
        for m in self.metrics:
            metric_product *= m
        extra_time_scale = (1 - metric_product / 1000000)
        exec_time = self.workload * (1 + 0.1 * extra_time_scale * math.exp(random.gauss(0, 1)))
        await asyncio.sleep(exec_time)

        self.result = random.normalvariate(0, 1)
        print(f"Client {self.id}: task {self.task_id} done! result: {self.result}")
    
    async def report(self):
        print(f"Client {self.id}: Report to job")

        client_report_msg = propius_pb2.client_report(client_id=self.id, result=self.result)
        self.job_stub.CLIENT_REPORT(client_report_msg)

        print(f"Client {self.id}: result reported")

    async def run(self, client_plotter=None):
        if client_plotter:
            await client_plotter.client_start()
        cm_offer = await self.checkin()
        if cm_offer.task_offer == 'NA':
            print(f"Client {self.id}: Not eligible, shutting down===")
            if client_plotter:
                await client_plotter.client_finish('drop')
            return
        cm_ack = await self.accept(cm_offer)
        if not cm_ack.ack:
            print(f"Client {self.id}: client manager not acknowledged, shutting down===")
            if client_plotter:
                await client_plotter.client_finish('drop')
            return
        job_ip, job_port = cm_ack.job_ip, cm_ack.job_port
        await self.request(job_ip, job_port)
        await self.execute()
        await self.report()
        if client_plotter:
            await client_plotter.client_finish('success')
        print(f"Client {self.id}: task {self.task_id} executed, shutting down===")
    

if __name__ == '__main__':
    global_setup_file = './global_config.yml'
    with open(global_setup_file, 'r') as gyamlfile:
        gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
        cm_ip, cm_port = gconfig['client_manager_ip'], int(gconfig['client_manager_port'])

        client = Client(0, 80, 80, 80, cm_ip, cm_port)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.run(None))