import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import random
import yaml
import pickle
from job.channels import parameter_server_pb2_grpc
from job.channels import parameter_server_pb2
from propius_client.propius_client import *
from commons import *
from collections import deque

class Client:
    def __init__(self, client_config: dict):
        self.id = -1
        self.task_id = -1
        self.propius_client_stub = Propius_client(client_config=client_config)
        self.ps_channel = None
        self.ps_stub = None
        
        #TODO execution duration
        self.execution_duration = 3
        self.event_queue = deque()
        self.meta_queue = deque()
        self.data_queue = deque()

        self.lock = asyncio.Lock()
    
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
        server_response = self.ps_stub.CLIENT_PING(client_id_msg)
        await self.handle_server_response(server_response)
    
    async def client_execute_complete(self, compl_event: str, status: bool, meta: str, data: str):
        client_complete_msg = parameter_server_pb2.client_complete(
            id=self.id,
            event=compl_event,
            status=status,
            meta=pickle.dumps(meta),
            data=pickle.dumps(data)
        )
        server_response = self.ps_stub.CLIENT_EXECUTE_COMPLETION(client_complete_msg)
        await self.handle_server_response(server_response)

    async def execute(self)->bool:
        async with self.lock:
            if len(self.event_queue) == 0:
                return
            event = self.event_queue.popleft()
            meta = self.meta_queue.popleft()
            data = self.data_queue.popleft()
        
        #TODO execute
        if event == CLIENT_TRAIN:
            await asyncio.sleep(self.execution_duration)
        elif event == SHUT_DOWN:
            return False
        compl_event = event
        status = True
        compl_meta = DUMMY_RESPONSE
        compl_data = DUMMY_RESPONSE
        await self.client_execute_complete(compl_event, status, compl_meta, compl_data)
        return True

    async def event_monitor(self):
        await self.client_ping()
        while await self.execute():
            await asyncio.sleep(1)

    async def cleanup_routines(self):
        try:
            self.propius_client_stub.close()
            await self.ps_channel.close()
        except Exception:
            pass

    async def run(self):
        try:
            self.propius_client_stub.connect()
            
            self.id, status, self.task_id, ps_ip, ps_port = await self.propius_client_stub.auto_assign(10)

            await self.propius_client_stub.close()
            
            if not status:
                return
            
            await self._connect_to_ps(ps_ip, ps_port)

            await self.event_monitor()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Client {self.id}: {e}")
        finally:
            await self.cleanup_routines()
        
if __name__ == '__main__':
    config_file = './evaluation/client/client_conf.yml'
    with open(config_file, 'r') as config:
        config = yaml.load(config, Loader=yaml.FullLoader)
        client = Client(config)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(client.run())
        loop.close()
     

