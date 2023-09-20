"""FL Job Manager Class."""

from propius.util import Msg_level, Propius_logger
from propius.job_manager.jm_monitor import JM_monitor
from propius.job_manager.jm_db_portal import JM_job_db_portal
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import asyncio
import pickle
import grpc

class Job_manager(propius_pb2_grpc.Job_managerServicer):
    def __init__(self, gconfig: dict, logger: Propius_logger):
        """Init job manager class. Connect to scheduler server

        Args:
            gconfig: global config file
                job_manager_ip
                job_manager_port
                job_db_ip
                job_db_port
                sched_alg
                job_public_constraint: name of public constraint
                job_private_constraint: name of private constraint
                job_expire_time
                sched_alg
                scheduler_ip
                scheduler_port
                logger
        """
        self.gconfig = gconfig
        self.ip = gconfig['job_manager_ip'] if not gconfig['use_docker'] else '0.0.0.0'
        self.port = int(gconfig['job_manager_port'])
        self.job_db_portal = JM_job_db_portal(gconfig, logger)
        self.jm_monitor = JM_monitor(gconfig['sched_alg'], logger, gconfig['plot'])
        self.sched_channel = None
        self.sched_portal = None
        self.logger = logger
        self._connect_sched(
            gconfig['scheduler_ip'], int(
                gconfig['scheduler_port']))
        self.sched_alg = gconfig['sched_alg']

        self.lock = asyncio.Lock()
        self.job_total_num = 0

    def _connect_sched(self, sched_ip: str, sched_port: int) -> None:
        if self.gconfig['use_docker']:
            sched_ip = 'scheduler'
        self.sched_channel = grpc.aio.insecure_channel(
            f'{sched_ip}:{sched_port}')
        self.sched_portal = propius_pb2_grpc.SchedulerStub(self.sched_channel)
        self.logger.print(
            f"Job manager: connecting to scheduler at {sched_ip}:{sched_port}", Msg_level.INFO)

    async def JOB_REGIST(self, request, context):
        """Insert job registration into database, return job_id assignment, and ack

        Args:
            request:
                job_info
        """
        est_demand = request.est_demand
        est_total_round = request.est_total_round
        job_ip, job_port = pickle.loads(request.ip), request.port
        public_constraint = pickle.loads(request.public_constraint)
        private_constraint = pickle.loads(request.private_constraint)

        async with self.lock:
            job_id = self.job_total_num
            self.job_total_num += 1

        ack = self.job_db_portal.register(
            job_id=job_id,
            public_constraint=public_constraint,
            private_constraint=private_constraint,
            job_ip=job_ip,
            job_port=job_port,
            total_demand=est_demand *
            est_total_round,
            total_round=est_total_round)
        
        self.logger.print(f"Job manager: ack job {job_id} register: {ack}, public constraint: {public_constraint}"
                     f", private constraint: {private_constraint}, demand: {est_demand}"
                     , Msg_level.INFO)
        if ack:
            await self.jm_monitor.job_register()
            if self.sched_alg != 'srdf' and self.sched_alg != 'srtf':
                await self.sched_portal.JOB_SCORE_UPDATE(propius_pb2.job_id(id=job_id))

        await self.jm_monitor.request()
        return propius_pb2.job_register_ack(id=job_id, ack=ack)

    async def JOB_REQUEST(self, request, context):
        """Update job metadata based on job round request. Returns ack

        Args:
            request:
                job_round_info
        """

        job_id, demand = request.id, request.demand
        ack = self.job_db_portal.request(job_id=job_id, demand=demand)
        if self.sched_alg == 'srdf' or self.sched_alg == 'srtf':
            await self.sched_portal.JOB_SCORE_UPDATE(propius_pb2.job_id(id=job_id))

        self.logger.print(f"Job manager: ack job {job_id} round request: {ack}", Msg_level.INFO)

        await self.jm_monitor.request()
        return propius_pb2.ack(ack=ack)

    async def JOB_END_REQUEST(self, request, context):
        """Update job metadata based on job round end request. Returns ack

        Args:
            request:
                job_id
        """

        job_id = request.id
        ack = self.job_db_portal.end_request(job_id=job_id)
        self.logger.print(f"Job manager: ack job {job_id} end round request: {ack}", Msg_level.INFO)

        await self.jm_monitor.request()
        return propius_pb2.ack(ack=ack)

    async def JOB_FINISH(self, request, context):
        """Remove job from database

        Args:
            request:
                job_id
        """

        job_id = request.id
        
        (constraints, demand, total_round, runtime, sched_latency) = \
            self.job_db_portal.finish(job_id)
        self.logger.print(f"Job manager: job {job_id} completed"
                          f", executed {total_round} rounds", Msg_level.INFO)

        if runtime:
            await self.jm_monitor.job_finish(constraints, demand, total_round, runtime, sched_latency)
        await self.jm_monitor.request()
        return propius_pb2.empty()
    
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