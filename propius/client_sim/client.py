import sys
[sys.path.append(i) for i in ['.', '..', '...']]
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
    def __init__(self, public_specifications:tuple, 
                 private_specifications:tuple,
                 gconfig):
        self.id = -1
        self.public_specifications = public_specifications
        self.private_specifications = private_specifications

        self.task_id = 0

        lb_ip = gconfig['load_balancer_ip']
        lb_port = gconfig['load_balancer_port']
        self.lb_channel = None
        self.lb_stub = None

        self._connect_lb(lb_ip, lb_port)

        self.job_channel = None
        self.job_stub = None
        self.workload = 0
        self.result = 0
        self.client_plotter = None

    def _connect_lb(self, lb_ip:str, lb_port:int)->None:
        self.lb_channel = grpc.aio.insecure_channel(f'{lb_ip}:{lb_port}')
        self.lb_stub = propius_pb2_grpc.Load_balancerStub(self.lb_channel)
        print(f"Client {self.id}: connecting to load balancer at {lb_ip}:{lb_port}")

    async def checkin(self)->propius_pb2.cm_offer:
        task_offer = None
        client_checkin_msg = propius_pb2.client_checkin(
            public_specification=pickle.dumps(self.public_specifications)
            )
        task_offer = await self.lb_stub.CLIENT_CHECKIN(client_checkin_msg)
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
        cm_ack = await self.lb_stub.CLIENT_ACCEPT(client_accept_msg)
        return cm_ack
    
    async def _connect_to_ps(self, job_ip:str, job_port:int):
        self.job_channel = grpc.aio.insecure_channel(f"{job_ip}:{job_port}")
        self.job_stub = propius_pb2_grpc.JobStub(self.job_channel)
        print(f"Client {self.id}: connecting to parameter server on {job_ip}:{job_port}")

    async def request(self)->bool:
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
        await self.job_stub.CLIENT_REPORT(client_report_msg)

        print(f"Client {self.id}: result reported")


    async def cleanup_routines(self):
        try:
            await self.lb_channel.close()
            await self.job_channel.close()
        except:
            pass

    async def run(self, client_plotter=None):
        self.client_plotter = client_plotter
        if client_plotter:
            await client_plotter.client_start()

        try:
            cm_offer = await self.checkin()
            self.id = cm_offer.client_id
            task_ids = pickle.loads(cm_offer.task_offer)
            task_private_constraint = pickle.loads(cm_offer.private_constraint)
            total_job_num = cm_offer.total_job_num
            print(f"Client {self.id}: recieve client manager offer: {task_ids}")

            await self.select_task(task_ids, task_private_constraint)
            if self.task_id == -1:
                print(f"Client {self.id}: not eligible, shutting down===")
                if total_job_num > 0 and client_plotter:
                    await client_plotter.client_finish('drop')
                await self.cleanup_routines()
                return
            
            cm_ack = await self.accept()
            if not cm_ack.ack:
                raise ValueError(f"client manager not acknowledged, shutting down===")
            
            job_ip, job_port = pickle.loads(cm_ack.job_ip), cm_ack.job_port
            ping_exp_time = cm_ack.ping_exp_time
            await self.lb_channel.close()

            await self._connect_to_ps(job_ip, job_port)
            
            start_time = time.time()
            job_ack = None

            while time.time() < start_time + ping_exp_time:
                job_ack = await self.request()
                if job_ack:
                    break
                await asyncio.sleep(max(2, min(10, ping_exp_time / 100)))
            if not job_ack:
                raise ValueError(f"not able to make requests to parameter server")

            await self.execute()
            await self.report()
            if client_plotter:
                await client_plotter.client_finish('success')
            print(f"Client {self.id}: task {self.task_id} executed, shutting down===")
        except Exception as e:
            print(f"Client {self.id}: {e}")
            if self.client_plotter:
                await self.client_plotter.client_finish('drop')
            await self.cleanup_routines()
        

if __name__ == '__main__':
    global_setup_file = './global_config.yml'
    with open(global_setup_file, 'r') as gyamlfile:
        gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
        client = Client((80, 80, 80), (), gconfig)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.run(None))