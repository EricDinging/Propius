import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import logging
import grpc
import yaml
from propius.channels import propius_pb2
from propius.channels import propius_pb2_grpc
from lb_analyzer import *

_cleanup_coroutines = []

class Load_balancer(propius_pb2_grpc.Load_balancerServicer):
    def __init__(self, gconfig):
        self.ip = gconfig['load_balancer_ip']
        self.port = gconfig['load_balancer_port']

        # Round robin
        self.idx = 0
        self.lock = asyncio.Lock()

        self.cm_addr_list = gconfig['client_manager']
        self.cm_channel_dict = {}
        self.cm_stub_dict = {}
        self._connect_cm()
        self.lb_analyzer = LB_analyzer(gconfig['sched_alg'], gconfig['total_running_second'])

    def _connect_cm(self):
        for cm_id, cm_addr in enumerate(self.cm_addr_list):
            cm_ip = cm_addr['ip']
            cm_port = cm_addr['port']
            self.cm_channel_dict[cm_id] = grpc.aio.insecure_channel(f'{cm_ip}:{cm_port}')
            self.cm_stub_dict[cm_id] = propius_pb2_grpc.Client_managerStub(self.cm_channel_dict[cm_id])
            print(f"Load balancer: connecting to client manager {cm_id} at {cm_ip}:{cm_port}")
    
    async def _disconnect_cm(self):
        async with self.lock:
            for cm_channel in self.cm_channel_dict.values():
                await cm_channel.close()

    def _next_idx(self):
        # locked
        self.idx = (self.idx + 1) % len(self.cm_channel_dict)

    async def CLIENT_CHECKIN(self, request, context):
        async with self.lock:
            await self.lb_analyzer.request()
            self.idx %= len(self.cm_channel_dict)
            print(f"Load balancer: recieve checkin request, route to client manager {self.idx}")
            return_msg = await self.cm_stub_dict[self.idx].CLIENT_CHECKIN(request)
            self._next_idx()
        return return_msg
    
    async def CLIENT_ACCEPT(self, request, context):
        async with self.lock:
            await self.lb_analyzer.request()
            self.idx %= len(self.cm_channel_dict)
            print(f"Load balancer: recieve client accept request, route to client manager {self.idx}")
            return_msg = await self.cm_stub_dict[self.idx].CLIENT_ACCEPT(request)
            self._next_idx()
        return return_msg

async def serve(gconfig):
    async def server_graceful_shutdown():
        print("Starting graceful shutdown...")
        load_balancer.lb_analyzer.report()
        await load_balancer._disconnect_cm()
        await server.stop(5)
    
    server = grpc.aio.server()
    load_balancer = Load_balancer(gconfig)
    propius_pb2_grpc.add_Load_balancerServicer_to_server(load_balancer, server)
    server.add_insecure_port(f'{load_balancer.ip}:{load_balancer.port}')
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.start()
    print(f"Load balancer: server started, listening on {load_balancer.ip}:{load_balancer.port}")
    await server.wait_for_termination()

if __name__== '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    global_setup_file = './global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            print(f"Load balancer read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig))
        except KeyboardInterrupt:
            pass   
        except Exception as e:
            logger.error(str(e))
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
    

