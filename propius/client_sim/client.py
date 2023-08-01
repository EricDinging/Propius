import grpc
import yaml
import random
import math
import asyncio
import pickle
import time
from propius.channels import propius_pb2
from propius.channels import propius_pb2_grpc
from propius.util.db import geq

class Client:
    def __init__(self, id:int, public_specifications:tuple, 
                 private_specifications:tuple,
                 cm_ip:str, cm_port:int):
        self.id = -1
        self.public_specifications = public_specifications
        self.private_specifications = private_specifications

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
        client_checkin_msg = propius_pb2.client_checkin(
            public_specification=pickle.dumps(self.public_specifications)
            )
        task_offer = self.cm_stub.CLIENT_CHECKIN(client_checkin_msg)
        return task_offer
    
    async def select_task(self, task_ids: list, private_constraints: list):
        for idx, id in enumerate(task_ids):
            if len(self.private_specifications) != len(private_constraints[idx]):
                raise ValueError("Client private specification len does not match required")
            if geq(self.private_specifications, private_constraints[idx]):
                self.task_id = id
                print(f"Client {self.id}: select task {id}")
                return
        self.task_id = -1
        print(f"Client {self.id}: not eligible")
        return
    
    async def accept(self)->propius_pb2.cm_ack:
        client_accept_msg = propius_pb2.client_accept(client_id=self.id, task_id=self.task_id)
        cm_ack = self.cm_stub.CLIENT_ACCEPT(client_accept_msg)
        return cm_ack
    
    async def _connect_to_ps(self, job_ip:str, job_port:int):
        self.job_channel = grpc.insecure_channel(f"{job_ip}:{job_port}")
        self.job_stub = propius_pb2_grpc.JobStub(self.job_channel)
    
    async def request(self)->bool:
        client_id_msg = propius_pb2.client_id(id=self.id)
        plan = self.job_stub.CLIENT_REQUEST(client_id_msg)
        ack = plan.ack
        if not ack:
            print(f"Client {self.id}: request job plan failed")
            return False
        self.workload = plan.workload
        print(f"Client {self.id}: request job plan, workload {self.workload}")
        return True

    async def execute(self):
        print(f"Client {self.id}: executing task {self.task_id}")
        metric_product = 1
        #TODO execute time calculation
        # for m in self.public_specifications:
        #     metric_product *= m
        # extra_time_scale = (1 - metric_product / 1000000)
        # exec_time = self.workload * (1 + 0.1 * extra_time_scale * math.exp(random.gauss(0, 1)))
        exec_time = self.workload
        await asyncio.sleep(exec_time)

        self.result = random.normalvariate(0, 1)
        print(f"Client {self.id}: task {self.task_id} done! result: {self.result}")
    
    async def report(self):
        print(f"Client {self.id}: Report to job")

        client_report_msg = propius_pb2.client_report(client_id=self.id, result=self.result)
        self.job_stub.CLIENT_REPORT(client_report_msg)

        print(f"Client {self.id}: result reported")

    def cleanup_routines(self):
        try:
            self.cm_channel.close()
            self.job_channel.close()
        except:
            pass

    async def run(self, client_plotter=None):
        if client_plotter:
            await client_plotter.client_start()
        cm_offer = await self.checkin()
        self.id = cm_offer.client_id
        task_ids = pickle.loads(cm_offer.task_offer)
        task_private_constraint = pickle.loads(cm_offer.private_constraint)
        print(f"Client {self.id}: recieve client manager offer: {task_ids}")

        await self.select_task(task_ids, task_private_constraint)
        if self.task_id == -1:
            print(f"Client {self.id}: Not eligible, shutting down===")
            if client_plotter:
                await client_plotter.client_finish('drop')
            return
        
        cm_ack = await self.accept()
        if not cm_ack.ack:
            print(f"Client {self.id}: client manager not acknowledged, shutting down===")
            if client_plotter:
                await client_plotter.client_finish('drop')
            return
        
        job_ip, job_port = pickle.loads(cm_ack.job_ip), cm_ack.job_port
        ping_exp_time = cm_ack.ping_exp_time
        self.cm_channel.close()

        start_time = time.time()
        job_ack = False
        await self._connect_to_ps(job_ip, job_port)
        while time.time() < start_time + ping_exp_time:
            job_ack = self.request()
            if job_ack:
                break
            await asyncio.sleep(5)
        if not job_ack:
            if client_plotter:
                await client_plotter.client_finish('drop')
            return
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

        client = Client(0, (80, 80, 80), (), cm_ip, cm_port)
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(client.run(None))
        finally:
            client.cleanup_routines()