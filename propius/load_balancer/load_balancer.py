"""Load Balancer class"""

from propius.util import Msg_level, Propius_logger
from propius.load_balancer.lb_monitor import LB_monitor
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import grpc
import asyncio

class Load_balancer(propius_pb2_grpc.Load_balancerServicer):
    def __init__(self, gconfig: dict, logger: Propius_logger):
        self.gconfig = gconfig
        self.ip = gconfig['load_balancer_ip'] if not gconfig['use_docker'] else '0.0.0.0'
        self.port = gconfig['load_balancer_port']
        self.id_weight = gconfig['client_manager_id_weight']
        self.logger = logger

        # Round robin
        self.idx = 0

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
        for cm_channel in self.cm_channel_dict.values():
            await cm_channel.close()

    def _next_idx(self):
        self.idx = (self.idx + 1) % len(self.cm_channel_dict)

    async def CLIENT_CHECKIN(self, request, context):
        return_msg = await self.cm_stub_dict[self.idx].CLIENT_CHECKIN(request)
        self._next_idx()
        await self.lb_monitor.request()
        return return_msg

    async def CLIENT_PING(self, request, context):
        idx = int(request.id / self.id_weight)
        return_msg =  await self.cm_stub_dict[idx].CLIENT_PING(request)
        await self.lb_monitor.request()
        return return_msg

    async def CLIENT_ACCEPT(self, request, context):
        idx = int(request.id / self.id_weight)
        return_msg = await self.cm_stub_dict[idx].CLIENT_ACCEPT(request)
        await self.lb_monitor.request()
        return return_msg
    
    async def HEART_BEAT(self, request, context):
        return propius_pb2.ack(ack=True)
    
    async def plot_routine(self):
        while True:
            self.lb_monitor.report()
            await asyncio.sleep(60)