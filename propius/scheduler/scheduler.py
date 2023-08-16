import sys
[sys.path.append(i) for i in ['.', '..', '...']]
from propius.util.commons import *
from propius.scheduler.sc_monitor import *
from propius.scheduler.sc_db_portal import *
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import asyncio
import yaml
import grpc

_cleanup_routines = []


class Scheduler(propius_pb2_grpc.SchedulerServicer):
    def __init__(self, gconfig):
        """Init scheduler class

        Args:
            gconfig global config dictionary
                scheduler_ip
                scheduler_port
                sched_alg
                irs_epsilon (apply to IRS algorithm)
                standard_round_time: default round execution time for SRTF
                job_public_constraint: name for constraint
                job_db_ip
                job_db_port
                sched_alg
                job_public_constraint: name of public constraint
                job_private_constraint: name of private constraint
                public_max: upper bound of the score
                job_expire_time
                client_manager: list of client manager address
                    ip:
                    client_db_port
                client_expire_time: expiration time of clients in the db
        """

        self.ip = gconfig['scheduler_ip']
        self.port = gconfig['scheduler_port']
        self.sched_alg = gconfig['sched_alg']
        if self.sched_alg == 'irs':
            self.irs_epsilon = float(gconfig['irs_epsilon'])
        self.job_db_portal = SC_job_db_portal(gconfig)
        self.client_db_portal = SC_client_db_portal(gconfig)

        self.public_max = gconfig['public_max']

        self.std_round_time = gconfig['standard_round_time']
        self.constraints = []
        self.public_constraint_name = gconfig['job_public_constraint']

        self.sc_monitor = SC_monitor(self.sched_alg)

    async def _irs_score(self, job_id: int):
        """Update all jobs' score in database according to IRS

        Args:
            job_id: id of job that has just been registered by job manager
        """

        constraints_client_map = {}
        constraints_job_map = {}
        constraints_denom_map = {}
        # get constraints
        constraints = self.job_db_portal.get_job_constraints(job_id)
        if not constraints:
            return propius_pb2.ack(ack=False)
        if constraints not in self.constraints:
            self.constraints.append(constraints)

        # search job for each group, remove if empty
        for cst in self.constraints:
            constraints_job_map[cst] = []
            if not self.job_db_portal.get_job_list(
                    cst, constraints_job_map[cst]):
                self.constraints.remove(cst)

        # search elig client size for each group
        for cst in self.constraints:
            constraints_client_map[cst] = self.client_db_portal.\
                get_client_proportion(cst)
        # sort constraints
        self.constraints.sort(key=lambda x: constraints_client_map[x])
        # get each client denominator
        client_size = self.client_db_portal.get_client_size()
        bq = ""
        for cst in self.constraints:
            this_q = ""
            for idx, name in enumerate(self.public_constraint_name):
                this_q += f"@{name}: [{cst[idx]}, {self.public_max[name]}] "

            q = this_q + bq
            constraints_denom_map[cst] = self.client_db_portal.get_irs_denominator(
                client_size, q)
            bq = bq + f"-{this_q}"

        # update all score
        custom_print("Scheduler: starting to update scores")
        for cst in self.constraints:
            try:
                custom_print(f"Scheduler: update score for {cst}: ")
                for idx, job in enumerate(constraints_job_map[cst]):
                    groupsize = len(constraints_job_map[cst])
                    self.job_db_portal.irs_update_score(
                        job,
                        groupsize,
                        idx,
                        constraints_denom_map[cst],
                        self.irs_epsilon,
                        self.std_round_time)
            except Exception as e:
                custom_print(e, WARNING)

    async def _irs2_score(self, job_id: int):
        """Update all jobs' score in database according to IRS2, a derivant from IRS

        Args:
            job_id: id of job that has just been registered by job manager
        """

        constraint_job_list = []
        constraint = self.job_db_portal.get_job_constraints(job_id)
        if not constraint:
            return propius_pb2.ack(ack=False)
        if not self.job_db_portal.get_job_list(
                constraint, constraint_job_list):
            return propius_pb2.ack(ack=False)
        client_prop = self.client_db_portal.get_client_proportion(constraint)

        custom_print(f"Scheduler: upd score for {constraint}: ")
        for idx, job in enumerate(constraint_job_list):
            groupsize = len(constraint_job_list)
            self.job_db_portal.irs_update_score(
                job, groupsize, idx, client_prop)

    async def JOB_SCORE_UPDATE(self, request, context) -> propius_pb2.ack:
        """Service function that update scores of job in database

        Args:
            request: job manager request message: job_id.id
            context:
        """
        job_id = request.id
        await self.sc_monitor.request_start(job_id)

        job_size = self.job_db_portal.get_job_size()

        if self.sched_alg == 'irs':
            # Update every job score using IRS
            await self._irs_score(job_id)
        elif self.sched_alg == 'irs2':
            # Update every job socre using IRS with a slight tweek that has experimental
            # performance improvement
            await self._irs2_score(job_id)

        elif self.sched_alg == 'fifo':
            # Give every job which doesn't have a score yet a score of
            # -timestamp
            self.job_db_portal.fifo_update_all_job_score()

        elif self.sched_alg == 'random':
            # Give every job which doesn't have a score yet a score of
            # a random float ranging from 0 to 10.
            self.job_db_portal.random_update_all_job_score()

        elif self.sched_alg == 'srdf':
            # Give every job a score of -remaining demand.
            # remaining demand = remaining round * current round demand
            # Prioritize job with the smallest remaining demand
            self.job_db_portal.srdf_update_all_job_score()

        elif self.sched_alg == 'srtf':
            # Give every job a score of -remaining time
            # remaining time = past avg round time * remaining round
            # Prioritize job with the shortest remaining demand
            self.job_db_portal.srtf_update_all_job_score(self.std_round_time)

        await self.sc_monitor.request_end(job_id, job_size)

        return propius_pb2.ack(ack=True)
    
    async def HEART_BEAT(self, request, context):
        return propius_pb2.ack(ack=True)


async def serve(gconfig):
    async def server_graceful_shutdown():
        custom_print("=====Scheduler shutting down=====")
        scheduler.sc_monitor.report()
        await server.stop(5)

    server = grpc.aio.server()
    scheduler = Scheduler(gconfig)
    propius_pb2_grpc.add_SchedulerServicer_to_server(scheduler, server)
    server.add_insecure_port(f'{scheduler.ip}:{scheduler.port}')
    await server.start()
    
    custom_print(f"Scheduler: server started, listening on {scheduler.ip}:{scheduler.port}, running {scheduler.sched_alg}")
    _cleanup_routines.append(server_graceful_shutdown())
    await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename='./propius/scheduler/app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

    global_setup_file = './propius/global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            print(f"{get_time()} scheduler read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            custom_print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_routines)
            loop.close()
