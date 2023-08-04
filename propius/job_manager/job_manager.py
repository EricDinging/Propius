import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import logging
import grpc
import yaml
from propius.channels import propius_pb2
from propius.channels import propius_pb2_grpc
from db_stub import *
from collections import deque
import asyncio
from jm_analyzer import *
import pickle

_cleanup_coroutines = []

class Job_manager(propius_pb2_grpc.Job_managerServicer):
    def __init__(self, gconfig):
        self.ip = gconfig['job_manager_ip']
        self.port = int(gconfig['job_manager_port'])
        self.job_db_stub = Job_db_stub(gconfig)
        self.jm_analyzer = JM_analyzer(gconfig['sched_alg'],
                                       gconfig['total_running_second'])
        self.sched_channel = None
        self.sched_stub = None
        self._connect_sched(gconfig['scheduler_ip'], int(gconfig['scheduler_port']))
        self.sched_alg = gconfig['sched_alg']

        self.lock = asyncio.Lock()
        self.job_total_num = 0

    def _connect_sched(self, sched_ip:str, sched_port:int)->None:
        self.sched_channel = grpc.aio.insecure_channel(f'{sched_ip}:{sched_port}')
        self.sched_stub = propius_pb2_grpc.SchedulerStub(self.sched_channel)
        print(f"Job manager: connecting to scheduler at {sched_ip}:{sched_port}")  

    async def JOB_REGIST(self, request, context):
        est_demand = request.est_demand
        est_total_round= request.est_total_round
        job_ip, job_port = pickle.loads(request.ip), request.port
        public_constraint = pickle.loads(request.public_constraint)
        private_constraint = pickle.loads(request.private_constraint)
        
        async with self.lock:
            job_id = self.job_total_num
            self.job_total_num += 1

        print(f"Job manager: job {job_id} check in, " +
              f"public constraint: {public_constraint}, "+
              f"private constraint: {private_constraint}")
        ack = self.job_db_stub.register(job_id=job_id,
                                        public_constraint=public_constraint,
                                        private_constraint=private_constraint, 
                                        job_ip=job_ip, job_port=job_port,
                                        total_demand=est_demand*est_total_round,
                                        total_round=est_total_round)
        print(f"Job manager: ack job {job_id} register: {ack}")
        if ack:
            await self.jm_analyzer.job_register()
            await self.sched_stub.JOB_SCORE_UPDATE(propius_pb2.job_id(id=job_id))
        else:
            await self.jm_analyzer.request()
        return propius_pb2.job_register_ack(id=job_id, ack=ack)
    
    async def JOB_REQUEST(self, request, context):
        job_id, demand = request.id, request.demand
        ack = self.job_db_stub.request(job_id=job_id, demand=demand)
        #await self.client_db_stub.cleanup()
        print(f"Job manager: ack job {job_id} round request: {ack}")
        if ack:
            await self.jm_analyzer.job_request()
        else:
            await self.jm_analyzer.request()
        return propius_pb2.ack(ack=ack)
    
    async def JOB_END_REQUEST(self, request, context):
        job_id = request.id
        ack = self.job_db_stub.end_request(job_id=job_id)
        print(f"Job manager: ack job {job_id} end round request: {ack}")
        await self.jm_analyzer.request()
        return propius_pb2.ack(ack=ack)
    
    async def JOB_FINISH(self, request, context):
        job_id = request.id
        print(f"Job manager: job {job_id} completed")
        (constraints, demand, total_round, runtime, sched_latency) = \
            self.job_db_stub.finish(job_id)

        if not runtime:
            await self.jm_analyzer.request()
        else:
            await self.jm_analyzer.job_finish(constraints, demand, total_round, runtime, sched_latency)
        return propius_pb2.empty()

async def serve(gconfig):
    async def server_graceful_shutdown():
        print("==Job manager ending==")
        logging.info("Starting graceful shutdown...")
        job_manager.jm_analyzer.report()
        job_manager.job_db_stub.flushdb()
        try:
            await job_manager.sched_channel.close()
        except:
            pass
        await server.stop(5)
    
    server = grpc.aio.server()
    job_manager = Job_manager(gconfig)
    propius_pb2_grpc.add_Job_managerServicer_to_server(job_manager, server)
    server.add_insecure_port(f'{job_manager.ip}:{job_manager.port}')
    await server.start()
    print(f"Job manager: server started, listening on {job_manager.ip}:{job_manager.port}")
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    global_setup_file = './global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            print("Job manager read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(str(e))
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()