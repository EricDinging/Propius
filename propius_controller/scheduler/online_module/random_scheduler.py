"""Random scheduler."""

from propius_controller.scheduler.online_module.base_scheduler import Scheduler
from propius_controller.util import Msg_level, Propius_logger
import random


class Random_scheduler(Scheduler):
    def __init__(self, gconfig: dict, logger: Propius_logger):
        super().__init__(gconfig, logger)

    async def online(self, job_id: int):
        """Give every job which doesn't have a score yet a random score

        Args:
            job_id: job id
        """
        score = random.uniform(0.0, 10.0)
        self.job_db_portal.set_score(score, job_id)
