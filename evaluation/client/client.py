import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import random
import yaml
import pickle
from evaluation.job.channels import parameter_server_pb2_grpc
from evaluation.job.channels import parameter_server_pb2
from propius_client.propius_client_aio import *
from evaluation.commons import *
from collections import deque
import time

class Client:
    def __init__(self, client_config: dict):
        self.id = client_config["id"]
        self.task_id = -1
        self.propius_client_stub = Propius_client_aio(client_config=client_config, verbose=True)
        self.ps_channel = None
        self.ps_stub = None
        
        #TODO execution duration
        self.execution_duration = 3
        self.event_queue = deque()
        self.meta_queue = deque()
        self.data_queue = deque()

        self.lock = asyncio.Lock()
        self.round = 0

        self.comp_speed = client_config["computation_speed"]
        self.comm_speed = client_config["communication_speed"]

        self.eval_start_time = client_config["eval_start_time"] if "eval_start_time" in client_config else time.time()
        self.cur_time = time.time() - self.eval_start_time
        self.active_time = client_config["active"]
        self.inactive_time = client_config["inactive"]
        self.cur_period = 0
    
    async def _connect_to_ps(self, ps_ip: str, ps_port: int):
        self.ps_channel = grpc.aio.insecure_channel(f"{ps_ip}:{ps_port}")
        self.ps_stub = parameter_server_pb2_grpc.Parameter_serverStub(self.ps_channel)
        print(
            f"Client {self.id}: connecting to parameter server on {ps_ip}:{ps_port}")
        
    async def handle_server_response(self, server_response: parameter_server_pb2.server_response):
        event = server_response.event
        meta = pickle.loads(server_response.meta)
        data = pickle.loads(server_response.data)
        #TODO load meta, data update model
        async with self.lock:
            self.event_queue.append(event)
            self.meta_queue.append(meta)
            self.data_queue.append(data)
        
    async def client_ping(self):
        client_id_msg = parameter_server_pb2.client_id(id=self.id)
        server_response = await self.ps_stub.CLIENT_PING(client_id_msg)

        await self.handle_server_response(server_response)
    
    async def client_execute_complete(self, compl_event: str, status: bool, meta: str, data: str):
        client_complete_msg = parameter_server_pb2.client_complete(
            id=self.id,
            event=compl_event,
            status=status,
            meta=pickle.dumps(meta),
            data=pickle.dumps(data)
        )
        server_response = await self.ps_stub.CLIENT_EXECUTE_COMPLETION(client_complete_msg)
        await self.handle_server_response(server_response)

    async def execute(self)->bool:
        async with self.lock:
            if len(self.event_queue) == 0:
                return
            event = self.event_queue.popleft()
            meta = self.meta_queue.popleft()
            data = self.data_queue.popleft()
    
        time = 0

        if event == CLIENT_TRAIN:
            time = 3 * meta["batch_size"] * meta["local_steps"] * float(self.comp_speed) / 1000
        elif event == SHUT_DOWN:
            return False
        elif event == UPDATE_MODEL:
            self.round = meta["round"]
            time = meta["download_size"] / float(self.comm_speed)

        elif event == UPLOAD_MODEL:
            time = meta["upload_size"] / float(self.comm_speed)
        
        print(f"Client {self.id}: Recieve {event} event, executing for {time} seconds")
        
        await asyncio.sleep(time)

        compl_event = event
        status = True
        compl_meta = {"round": self.round}
        compl_data = DUMMY_RESPONSE
        
        await self.client_execute_complete(compl_event, status, compl_meta, compl_data)
        return True

    async def event_monitor(self):
        print(f"Client {self.id}: ping")
        await self.client_ping()
        while await self.execute():
            await asyncio.sleep(1)

    async def cleanup_routines(self, propius=False):
        try:
            if propius:
                await self.propius_client_stub.close()
            await self.ps_channel.close()
        except Exception:
            pass

    async def run(self):
        try:
            while True:
                if self.cur_period >= len(self.active_time):
                    print(f"Client {self.id}: ==shutting down==")
                    break
                self.cur_time = time.time() - self.eval_start_time
                if self.cur_time < self.active_time[self.cur_period]:
                    sleep_time = self.active_time[self.cur_period] - self.cur_time
                    print(f"Client {self.id}: sleep for {sleep_time}")
                    await asyncio.sleep(self.active_time[self.cur_period] - self.cur_time)
                    continue
                elif self.cur_time >= self.inactive_time[self.cur_period]:
                    self.cur_period += 1
                    continue
                
                await self.propius_client_stub.connect()
                
                result = await self.propius_client_stub.auto_assign(0)

                _, status, self.task_id, ps_ip, ps_port = result

                await self.propius_client_stub.close()
                
                if not status:
                    await asyncio.sleep(10)
                    continue

                self.cur_time = time.time() - self.eval_start_time
                remain_time = self.inactive_time[self.cur_period] - self.cur_time
                if remain_time <= 0:
                    continue
                
                await self._connect_to_ps(ps_ip, ps_port)
                try:
                    task = asyncio.create_task(self.event_monitor())
                    await asyncio.wait_for(task, 
                                           timeout=remain_time)
                except asyncio.TimeoutError:
                    print(f"Client {self.id}: timeout, abort")
                    pass
                await self.cleanup_routines()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Client {self.id}: {e}")
        finally:
            await self.cleanup_routines(True)
        
if __name__ == '__main__':
    config_file = './evaluation/client/client_conf.yml'
    with open(config_file, 'r') as config:
        config = yaml.load(config, Loader=yaml.FullLoader)
        client = Client(config)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.run())
        loop.close()
     

