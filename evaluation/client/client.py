import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import pickle
from evaluation.job.channels import parameter_server_pb2_grpc
from evaluation.job.channels import parameter_server_pb2
from propius.client.propius_client_aio import *
from evaluation.commons import *
from collections import deque
import time

class Client:
    def __init__(self, client_config: dict):
        self.id = client_config["id"]
        self.task_id = -1
        self.use_docker = client_config["use_docker"]

        if client_config["use_docker"]:
            client_config["load_balancer_ip"] = "load_balancer"
            
        self.propius_client_stub = Propius_client_aio(
            client_config=client_config, 
            verbose=False,
            logging=True)
        
        self.ps_channel = None
        self.ps_stub = None
        
        self.execution_duration = 3
        self.event_queue = deque()
        self.meta_queue = deque()
        self.data_queue = deque()
        self.round = 0

        self.comp_speed = client_config["computation_speed"]
        self.comm_speed = client_config["communication_speed"]

        self.eval_start_time = client_config["eval_start_time"] if "eval_start_time" in client_config else time.time()
        self.active_time = client_config["active"]
        self.inactive_time = client_config["inactive"]
        self.cur_period = 0
        self.speedup_factor = client_config["speedup_factor"]
    
    async def _connect_to_ps(self, ps_ip: str, ps_port: int):
        self.ps_channel = grpc.aio.insecure_channel(f"{ps_ip}:{ps_port}")
        self.ps_stub = parameter_server_pb2_grpc.Parameter_serverStub(self.ps_channel)
        custom_print(
            f"Client {self.id}: connecting to parameter server on {ps_ip}:{ps_port}")
        
    async def handle_server_response(self, server_response: parameter_server_pb2.server_response):
        event = server_response.event
        meta = pickle.loads(server_response.meta)
        data = pickle.loads(server_response.data)
        self.event_queue.append(event)
        self.meta_queue.append(meta)
        self.data_queue.append(data)
        
    async def client_ping(self)->bool:
        client_id_msg = parameter_server_pb2.client_id(id=self.propius_client_stub.id)
        server_response = await self.ps_stub.CLIENT_PING(client_id_msg)
        if server_response.event == DUMMY_EVENT:
            return True
        await self.handle_server_response(server_response)
        return False
    
    async def client_execute_complete(self, compl_event: str, status: bool, meta: str, data: str):
        client_complete_msg = parameter_server_pb2.client_complete(
            id=self.propius_client_stub.id,
            event=compl_event,
            status=status,
            meta=pickle.dumps(meta),
            data=pickle.dumps(data)
        )
        server_response = await self.ps_stub.CLIENT_EXECUTE_COMPLETION(client_complete_msg)
        await self.handle_server_response(server_response)

    async def execute(self)->bool:
        if len(self.event_queue) == 0:
            return
        event = self.event_queue.popleft()
        meta = self.meta_queue.popleft()
        data = self.data_queue.popleft()
    
        exe_time = 0

        if event == CLIENT_TRAIN:
            exe_time = 3 * meta["batch_size"] * meta["local_steps"] * float(self.comp_speed) / 1000
        elif event == SHUT_DOWN:
            return False
        elif event == UPDATE_MODEL:
            self.round = meta["round"]
            exe_time = meta["download_size"] / float(self.comm_speed)

        elif event == UPLOAD_MODEL:
            exe_time = meta["upload_size"] / float(self.comm_speed)
        
        exe_time /= self.speedup_factor
        custom_print(f"Client {self.id}: Recieve {event} event, executing for {exe_time} seconds", INFO)
        await asyncio.sleep(exe_time)

        compl_event = event
        status = True
        compl_meta = {"round": self.round, "exec_id": self.id}
        compl_data = DUMMY_RESPONSE
        
        await self.client_execute_complete(compl_event, status, compl_meta, compl_data)
        return True
    
    def remain_time(self) -> float:
        cur_time = time.time() - self.eval_start_time
        remain_time = self.inactive_time[self.cur_period] - cur_time
        return remain_time

    async def event_monitor(self) -> bool:
        
        while await self.client_ping():
            await asyncio.sleep(3)
            
        while await self.execute():
            await asyncio.sleep(3)
        return True

    async def cleanup_routines(self, propius=False):
        try:
            if propius:
                await self.propius_client_stub.close()
                custom_print(f"Client {self.id}: ==shutting down==", ERROR)
            await self.ps_channel.close()
        except Exception:
            pass

    async def run(self):
        while True:
            try:
                if self.cur_period >= len(self.active_time) or \
                    self.cur_period >= len(self.inactive_time):
                    custom_print(f"Client {self.id}: ==shutting down==", WARNING)
                    break
                cur_time = time.time() - self.eval_start_time

                if self.active_time[self.cur_period] > self.inactive_time[self.cur_period]:
                    custom_print(f"Period: {self.cur_period}", ERROR)
                    custom_print(f"Active time: {self.active_time}", ERROR)
                    custom_print(f"Inactive time: {self.inactive_time}", ERROR)
                    break
                
                if cur_time < self.active_time[self.cur_period]:
                    sleep_time = self.active_time[self.cur_period] - cur_time
                    # custom_print(f"Client {self.id}: sleep for {sleep_time}")
                    await asyncio.sleep(sleep_time)
                    continue
                elif cur_time >= self.inactive_time[self.cur_period]:
                    self.cur_period += 1
                    continue

                
                remain_time = self.remain_time()
                if remain_time <= 600 / self.speedup_factor:
                    await asyncio.sleep(remain_time)
                
                await self.propius_client_stub.connect()

                result = await self.propius_client_stub.auto_assign(0)

                _, status, self.task_id, ps_ip, ps_port = result

                await self.propius_client_stub.close()
                
                if not status:
                    sleep_time = 20
                    sleep_time /= self.speedup_factor
                    await asyncio.sleep(sleep_time)
                    continue
                
                await self._connect_to_ps(ps_ip, ps_port)
                if not await self.event_monitor():
                    custom_print(f"Client {self.id}: timeout, aborted", WARNING)
                await self.cleanup_routines()

            except KeyboardInterrupt:
                break
            except Exception as e:
                custom_print(f"Client {self.id}: {e}", ERROR)
            
        await self.cleanup_routines(True)
        
if __name__ == '__main__':
    config_file = './evaluation/client/client_conf.yml'
    with open(config_file, 'r') as config:
        config = yaml.load(config, Loader=yaml.FullLoader)
        if len(sys.argv) != 2:
            custom_print(f"Usage: python evaluation/client/client.py <id>", ERROR)
            exit(1)
        config["id"] = int(sys.argv[1])
        eval_config_file = './evaluation/evaluation_config.yml'
        with open(eval_config_file, 'r') as eval_config:
            eval_config = yaml.load(eval_config, Loader=yaml.FullLoader)
            config["load_balancer_ip"] = eval_config["load_balancer_ip"]
            config["load_balancer_port"] = eval_config["load_balancer_port"]
            config["use_docker"] = eval_config["use_docker"]
            client = Client(config)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(client.run())
            loop.close()
     

