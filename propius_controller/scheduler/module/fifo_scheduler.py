"""FIFO scheduler."""

from propius_controller.scheduler.module.base_scheduler import Scheduler
from propius_controller.util import Msg_level, Propius_logger

class FIFO_scheduler(Scheduler):
    def __init__(self, gconfig: dict, logger: Propius_logger):
        super().__init__(gconfig, logger)

    async def online(self, job_id: int):
        """Give every job which doesn't have a score yet a score of -timestamp

        Returns:
            boolean indicating whether there is a score updated
        """
        
        job_timestamp = int(self.job_db_portal.get_field(job_id, "timestamp"))

        score = - (job_timestamp - self.start_time)
        self.job_db_portal.set_score(score, job_id)
        
