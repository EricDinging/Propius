"""Job base scheduler class."""

from abc import ABC, abstractmethod
from propius_controller.util import Msg_level, Propius_logger
from propius_controller.scheduler.sc_monitor import SC_monitor
from propius_controller.scheduler.sc_db_portal import (
    SC_client_db_portal,
    SC_job_db_portal,
)
from propius_controller.scheduler.sc_job_group import SC_job_group_manager
from propius_controller.channels import propius_pb2_grpc
from propius_controller.channels import propius_pb2
import pickle
import asyncio
import time


class Scheduler(propius_pb2_grpc.SchedulerServicer):
    def __init__(self, gconfig: dict, logger: Propius_logger):
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
            logger
        """

        self.ip = gconfig["scheduler_ip"] if not gconfig["use_docker"] else "0.0.0.0"
        self.port = gconfig["scheduler_port"]

        # TODO move to main
        # self.sched_alg = gconfig["sched_alg"]
        # if self.sched_alg == "irs":
        #     self.irs_epsilon = float(gconfig["irs_epsilon"])

        self.job_db_portal = SC_job_db_portal(gconfig, logger)
        self.client_db_portal = SC_client_db_portal(gconfig, logger)

        self.public_max = gconfig["public_max"]

        # self.std_round_time = gconfig["standard_round_time"]
        # self.constraints = []
        self.public_constraint_name = gconfig["job_public_constraint"]

        self.sc_monitor = SC_monitor(
            logger, gconfig["scheduler_plot_path"], gconfig["plot"]
        )
        self.logger = logger

        self.start_time = time.time()

        # self.job_group_manager = SC_job_group_manager(
        #     self.job_db_portal,
        #     self.client_db_portal,
        #     self.public_constraint_name,
        #     self.public_max,
        #     logger,
        # )

    @abstractmethod
    async def online(self):
        pass

    @abstractmethod
    async def offline(self):
        pass

    async def JOB_SCORE_UPDATE(self, request, context) -> propius_pb2.ack:
        """Service function that update scores of job in database

        Args:
            request: job manager request message: job_id.id
            context:
        """
        job_id = request.id

        await self.sc_monitor.request(job_id)

        # job_size = self.job_db_portal.get_job_size()

        self.logger.print("Receive update score request", Msg_level.INFO)

        await self.online(job_id)

        # if self.sched_alg == "irs":
        #     # Update every job score using IRS
        #     await self._irs_score(job_id)
        # elif self.sched_alg == "irs2":
        #     # Update every job socre using IRS with a slight tweek that has experimental
        #     # performance improvement
        #     await self._irs2_score(job_id)

        # elif self.sched_alg == "irs3":
        #     # Update every job score using IRS
        #     self.job_group_manager.update_job_group(job_id != -1, job_id)

        # elif self.sched_alg == "srsf":
        #     # Give every job a score of -remaining demand.
        #     # remaining demand = remaining round * current round demand
        #     # Prioritize job with the smallest remaining demand
        #     self.job_db_portal.srsf_update_all_job_score()

        # elif self.sched_alg == "srtf":
        #     # Give every job a score of -remaining time
        #     # remaining time = past avg round time * remaining round
        #     # Prioritize job with the shortest remaining demand
        #     self.job_db_portal.srtf_update_all_job_score(self.std_round_time)

        # elif self.sched_alg == "las":
        #     # Give every job a score of -attained service
        #     self.job_db_portal.las_update_all_job_score()

        return propius_pb2.ack(ack=True)

    async def GET_JOB_GROUP(self, request, context):
        return propius_pb2.group_info(
            group=pickle.dumps(self.job_group_manager.fetch_job_group())
        )

    async def HEART_BEAT(self, request, context):
        return propius_pb2.ack(ack=True)

    async def plot_routine(self):
        while True:
            self.sc_monitor.report()
            await asyncio.sleep(60)
