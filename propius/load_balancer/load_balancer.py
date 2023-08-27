import sys
[sys.path.append(i) for i in ['.', '..', '...']]
from propius.util.commons import *
from propius.load_balancer.lb_monitor import *
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import yaml
import grpc
import logging
import logging.handlers
import asyncio

_cleanup_coroutines = []


class Load_balancer(propius_pb2_grpc.Load_balancerServicer):
    def __init__(self, gconfig):
        self.gconfig = gconfig
        self.ip = gconfig['load_balancer_ip'] if not gconfig['use_docker'] else '0.0.0.0'
        self.port = gconfig['load_balancer_port']
        self.id_weight = gconfig['client_manager_id_weight']

        # Round robin
        self.idx = 0
        self.lock = asyncio.Lock()

        self.cm_num = len(gconfig['client_manager'])
        self.cm_addr_list = gconfig['client_manager']
        self.cm_channel_dict = {}
        self.cm_stub_dict = {}
        self._connect_cm()
        self.lb_monitor = LB_monitor(gconfig['sched_alg'], gconfig['plot'])

    def _connect_cm(self):
        for cm_id, cm_addr in enumerate(self.cm_addr_list):
            if cm_id >= self.cm_num:
                break
            if self.gconfig['use_docker']:
                cm_ip = f'client_manager_{cm_id}'
            else:
                cm_ip = cm_addr['ip']
            cm_port = cm_addr['port']
            self.cm_channel_dict[cm_id] = grpc.aio.insecure_channel(
                f'{cm_ip}:{cm_port}')
            self.cm_stub_dict[cm_id] = propius_pb2_grpc.Client_managerStub(
                self.cm_channel_dict[cm_id])
            # custom_print(
            #     f"Load balancer: connecting to client manager {cm_id} at {cm_ip}:{cm_port}")

    async def _disconnect_cm(self):
        async with self.lock:
            for cm_channel in self.cm_channel_dict.values():
                await cm_channel.close()

    def _next_idx(self):
        # locked
        self.idx = (self.idx + 1) % len(self.cm_channel_dict)

    async def CLIENT_CHECKIN(self, request, context):
        async with self.lock:
            await self.lb_monitor.request()
            self.idx %= len(self.cm_channel_dict)
            # custom_print(
            #     f"Load balancer: client check in, route to client manager {self.idx}")
            return_msg = await self.cm_stub_dict[self.idx].CLIENT_CHECKIN(request)
            self._next_idx()
        return return_msg

    async def CLIENT_PING(self, request, context):
        async with self.lock:
            await self.lb_monitor.request()
            idx = int(request.id / self.id_weight)
            # custom_print(
            #     f"Load balancer: client ping, route to client manager {idx}")
            return_msg = await self.cm_stub_dict[idx].CLIENT_PING(request)
        return return_msg

    async def CLIENT_ACCEPT(self, request, context):
        async with self.lock:
            await self.lb_monitor.request()
            self.idx %= len(self.cm_channel_dict)
            # custom_print(
            #     f"Load balancer: client accept, route to client manager {self.idx}")
            return_msg = await self.cm_stub_dict[self.idx].CLIENT_ACCEPT(request)
            self._next_idx()
        return return_msg
    
    async def HEART_BEAT(self, request, context):
        return propius_pb2.ack(ack=True)
    
    async def heartbeat_routine(self):
        try:
            while True:
                await asyncio.sleep(30)
                try:
                    self.sched_portal.HEART_BEAT(propius_pb2.empty())
                except:
                    pass
        except asyncio.CancelledError:
            pass


async def serve(gconfig):
    async def server_graceful_shutdown():
        custom_print(f"=====Load balancer shutting down=====", WARNING)
        load_balancer.lb_monitor.report()

        heartbeat_task.cancel()
        await heartbeat_task

        await load_balancer._disconnect_cm()
        await server.stop(5)

    server = grpc.aio.server()
    load_balancer = Load_balancer(gconfig)
    propius_pb2_grpc.add_Load_balancerServicer_to_server(load_balancer, server)
    server.add_insecure_port(f'{load_balancer.ip}:{load_balancer.port}')
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.start()
    custom_print(f"Load balancer: server started, listening on {load_balancer.ip}:{load_balancer.port}", INFO)

    heartbeat_task = asyncio.create_task(load_balancer.heartbeat_routine())

    await server.wait_for_termination()

if __name__ == '__main__':
    log_file = './propius/load_balancer/app.log'
    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    global_setup_file = './propius/global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            custom_print(f"Load balancer read config successfully", INFO)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            custom_print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
