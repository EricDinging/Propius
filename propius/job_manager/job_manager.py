import sys
[sys.path.append(i) for i in ['.', '..', '...']]
from propius.util.commons import *
from propius.job_manager.jm_monitor import *
from propius.job_manager.jm_db_portal import *
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import asyncio
from collections import deque
import pickle
import yaml
import grpc

_cleanup_coroutines = []


class Job_manager(propius_pb2_grpc.Job_managerServicer):
    def __init__(self, gconfig, logger):
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
            f"Job manager: connecting to scheduler at {sched_ip}:{sched_port}", INFO)

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
                     , INFO)
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

        self.logger.print(f"Job manager: ack job {job_id} round request: {ack}", INFO)

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
        self.logger.print(f"Job manager: ack job {job_id} end round request: {ack}", INFO)

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
                          f", executed {total_round} rounds", INFO)

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


async def serve(gconfig, logger):
    async def server_graceful_shutdown():
        logger.print(f"=====Job manager shutting down=====", WARNING)
        job_manager.jm_monitor.report()
        job_manager.job_db_portal.flushdb()

        heartbeat_task.cancel()
        await heartbeat_task

        try:
            await job_manager.sched_channel.close()
        except Exception as e:
            logger.print(e, WARNING)
        await server.stop(5)

    # def sigterm_handler(signum, frame):
    #     loop = asyncio.get_event_loop()
    #     loop.run_until_complete(server_graceful_shutdown())
    #     loop.stop()

    server = grpc.aio.server()
    job_manager = Job_manager(gconfig, logger)
    propius_pb2_grpc.add_Job_managerServicer_to_server(job_manager, server)
    server.add_insecure_port(f'{job_manager.ip}:{job_manager.port}')
    await server.start()

    heartbeat_task = asyncio.create_task(job_manager.heartbeat_routine())

    logger.print(f"Job manager: server started, listening on {job_manager.ip}:{job_manager.port}", INFO)
    _cleanup_coroutines.append(server_graceful_shutdown())

    # signal.signal(signal.SIGTERM, sigterm_handler)

    await server.wait_for_termination()

if __name__ == '__main__':
    log_file = './propius/monitor/log/jm.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    global_setup_file = './propius/global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            logger = My_logger(log_file=log_file, verbose=gconfig["verbose"], use_logging=True)
            logger.print(f"Job manager read config successfully", INFO)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig, logger))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
