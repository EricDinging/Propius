"""Load Balancer class"""

from propius.util.commons import Msg_level, My_logger
from propius.load_balancer.lb_monitor import LB_monitor
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import grpc
import asyncio

class Load_balancer(propius_pb2_grpc.Load_balancerServicer):
    def __init__(self, gconfig: dict, logger: My_logger):
        self.gconfig = gconfig
        self.ip = gconfig['load_balancer_ip'] if not gconfig['use_docker'] else '0.0.0.0'
        self.port = gconfig['load_balancer_port']
        self.id_weight = gconfig['client_manager_id_weight']
        self.logger = logger

        # Round robin
        self.idx = 0
        self.lock = asyncio.Lock()

        self.cm_num = len(gconfig['client_manager'])
        self.cm_addr_list = gconfig['client_manager']
        self.cm_channel_dict = {}
        self.cm_stub_dict = {}
        self._connect_cm()
        self.lb_monitor = LB_monitor(gconfig['sched_alg'], logger, gconfig['plot'])

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
            # self.logger.print(
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
            # self.logger.print(
            #     f"Load balancer: client check in, route to client manager {self.idx}")
            return_msg = await self.cm_stub_dict[self.idx].CLIENT_CHECKIN(request)
            self._next_idx()
        return return_msg

    async def CLIENT_PING(self, request, context):
        async with self.lock:
            await self.lb_monitor.request()
            idx = int(request.id / self.id_weight)
            # self.logger.print(
            #     f"Load balancer: client ping, route to client manager {idx}")
            return_msg = await self.cm_stub_dict[idx].CLIENT_PING(request)
        return return_msg

    async def CLIENT_ACCEPT(self, request, context):
        async with self.lock:
            await self.lb_monitor.request()
            self.idx %= len(self.cm_channel_dict)
            # self.logger.print(
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