import sys
[sys.path.append(i) for i in ['.', '..', '...']]

import logging
import grpc
import yaml
from propius.channels import propius_pb2
from propius.channels import propius_pb2_grpc
from propius.scheduler.db_stub import *
import asyncio
from propius.scheduler.sc_analyzer import *

_cleanup_routines = []

class Scheduler(propius_pb2_grpc.SchedulerServicer):
    def __init__(self, gconfig):
        self.ip = gconfig['scheduler_ip']
        self.port = gconfig['scheduler_port']
        self.sched_alg = gconfig['sched_alg']
        if self.sched_alg == 'irs':
            self.irs_epsilon = float(gconfig['irs_epsilon'])
        self.job_db_stub = Job_db_stub(gconfig)
        self.client_db_stub = Client_db_stub(gconfig)
        
        self.metric_scale = gconfig['metric_scale']
        self.std_round_time = gconfig['standard_round_time']
        self.constraints = []
        self.public_constraint_name = gconfig['job_public_constraint']

        self.sc_analyzer = SC_analyzer(self.sched_alg, gconfig['total_running_second'])

    async def _irs_score(self, job_id:int):
        constraints_client_map = {}
        constraints_job_map = {}
        constraints_denom_map = {}
        # get constraints
        constraints = self.job_db_stub.get_job_constraints(job_id)
        if not constraints:
            return propius_pb2.ack(ack=False)
        if constraints not in self.constraints:
            self.constraints.append(constraints)
        # search job for each group, remove if empty
        for cst in self.constraints:
            constraints_job_map[cst] = []
            if not self.job_db_stub.get_job_list(cst, constraints_job_map[cst]):
                self.constraints.remove(cst)
        # search elig client size for each group
        for cst in self.constraints:
            constraints_client_map[cst] = self.client_db_stub.get_client_proportion(cst)
        # sort constraints
        self.constraints.sort(key=lambda x: constraints_client_map[x])
        # get each client denominator
        client_size = self.client_db_stub.get_client_size()
        bq = ""
        for cst in self.constraints:            
            this_q = ""
            for idx, name in enumerate(self.public_constraint_name):
                this_q += f"@{name}: [{cst[idx]}, {self.metric_scale}] "

            q = this_q + bq
            constraints_denom_map[cst] = self.client_db_stub.get_irs_denominator(client_size, cst, q)
            bq = bq + f"-{this_q}"
        # update all score
        for cst in self.constraints:
            try:
                print(f"Scheduler: upd score for {cst}: ")
                for idx, job in enumerate(constraints_job_map[cst]):
                    groupsize = len(constraints_job_map[cst])
                    self.job_db_stub.irs_update_score(job, groupsize, idx, constraints_denom_map[cst], self.irs_epsilon, self.std_round_time)
            except:
                pass
        return propius_pb2.ack(ack=False)

    async def _irs_score(self, job_id:int):
        constraint_job_list = []
        constraint = self.job_db_stub.get_job_constraints(job_id)
        if not constraint:
            return propius_pb2.ack(ack=False)
        if not self.job_db_stub.get_job_list(constraint, constraint_job_list):
            return propius_pb2.ack(ack=False)
        client_prop = self.client_db_stub.get_client_proportion(constraint)

        print(f"Scheduler: upd score for {constraint}: ")
        for idx, job in enumerate(constraint_job_list):
            groupsize = len(constraint_job_list)
            self.job_db_stub.irs_update_score(job, groupsize, idx, client_prop)
        return propius_pb2.ack(ack=False)
        

    async def JOB_SCORE_UPDATE(self, request, context):
        job_id = request.id
        await self.sc_analyzer.request_start(job_id)
        job_size = self.job_db_stub.get_job_size()

        if self.sched_alg == 'irs':
            await self._irs_score(job_id)
        elif self.sched_alg == 'irs2':
            await self._irs2_score(job_id)
        elif self.sched_alg == 'fifo':
            self.job_db_stub.fifo_update_all_job_score()
        elif self.sched_alg == 'random':
            self.job_db_stub.random_update_all_job_score()
        elif self.sched_alg == 'srdf':
            self.job_db_stub.srdf_update_all_job_score()
        elif self.sched_alg == 'srtf':
            self.job_db_stub.srtf_update_all_job_score(self.std_round_time)
        await self.sc_analyzer.request_end(job_id, job_size)
        return propius_pb2.ack(ack=True)
    
async def serve(gconfig):
    async def server_graceful_shutdown():
        print("==Scheduler ending==")
        logging.info("Starting graceful shutdown...")
        scheduler.sc_analyzer.report()
        await server.stop(5)

    server = grpc.aio.server()
    scheduler = Scheduler(gconfig)
    propius_pb2_grpc.add_SchedulerServicer_to_server(scheduler, server)
    server.add_insecure_port(f'{scheduler.ip}:{scheduler.port}')
    await server.start()
    print(f"Scheduler: server started, listening on {scheduler.ip}:{scheduler.port}, running {scheduler.sched_alg}")
    _cleanup_routines.append(server_graceful_shutdown())
    await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    global_setup_file = './global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            print("scheduler read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(str(e))
        finally:
            loop.run_until_complete(*_cleanup_routines)
            loop.close()