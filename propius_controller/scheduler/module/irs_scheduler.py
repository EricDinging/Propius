"""IRS scheduler."""

from propius_controller.scheduler.module.base_scheduler import Scheduler
from propius_controller.util import Msg_level, Propius_logger


class IRS_scheduler(Scheduler):
    def __init__(self, gconfig: dict, logger: Propius_logger):
        super().__init__(gconfig, logger)

        self.sched_alg = gconfig["sched_alg"]
        if self.sched_alg == "irs":
            self.irs_epsilon = float(gconfig["irs_epsilon"])

    async def online(self, job_id: int):
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
            if not self.job_db_portal.get_job_list(cst, constraints_job_map[cst]):
                self.constraints.remove(cst)

        # search elig client size for each group
        for cst in self.constraints:
            constraints_client_map[cst] = self.client_db_portal.get_client_proportion(
                cst
            )
        # sort constraints
        self.constraints.sort(key=lambda x: constraints_client_map[x])
        # get each client denominator
        client_size = self.client_db_portal.get_client_size()
        bq = ""
        for cst in self.constraints:
            this_q = "("
            for idx, name in enumerate(self.public_constraint_name):
                this_q += f"@{name}: [{cst[idx]}, {self.public_max[name]}] "
            this_q += ") "

            q = this_q + bq
            constraints_denom_map[cst] = self.client_db_portal.get_irs_denominator(
                client_size, q
            )
            bq = bq + f" -({this_q})"

        # update all score
        self.logger.print("Scheduler: starting to update scores", Msg_level.INFO)
        for cst in self.constraints:
            try:
                self.logger.print(
                    f"Scheduler: update score for {cst}: ", Msg_level.INFO
                )
                for idx, job in enumerate(constraints_job_map[cst]):
                    groupsize = len(constraints_job_map[cst])
                    self.job_db_portal.irs_update_score(
                        job,
                        groupsize,
                        idx,
                        constraints_denom_map[cst],
                        self.irs_epsilon,
                        self.std_round_time,
                    )
            except Exception as e:
                self.logger.print(e, Msg_level.WARNING)

    async def _irs2_score(self, job_id: int):
        """Update all jobs' score in database according to IRS2, a derivant from IRS

        Args:
            job_id: id of job that has just been registered by job manager
        """

        # get constraints
        constraints = self.job_db_portal.get_job_constraints(job_id)
        if not constraints:
            return propius_pb2.ack(ack=False)
        if constraints not in self.constraints:
            self.constraints.append(constraints)

        # search job for each group, remove if empty
        for cst in self.constraints:
            try:
                constraints_job_list = []
                if not self.job_db_portal.get_job_list(cst, constraints_job_list):
                    self.constraints.remove(cst)
                    continue

                client_prop = self.client_db_portal.get_client_proportion(cst)

                self.logger.print(f"Scheduler: upd score for {cst}: ", Msg_level.INFO)
                groupsize = len(constraints_job_list)
                for idx, job in enumerate(constraints_job_list):
                    self.job_db_portal.irs_update_score(
                        job, groupsize, idx, client_prop
                    )

            except Exception as e:
                self.logger.print(e, Msg_level.WARNING)
