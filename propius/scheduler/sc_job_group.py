"""Scheduler job group manager"""

from propius.util.commons import Job_group
from propius.scheduler.sc_db_portal import SC_job_db_portal

class SC_job_group_manager:
    def __init__(self, job_db_portal: SC_job_db_portal):
        self.job_group = Job_group()
        self.job_db_portal = job_db_portal

    def update_job_(self):
        pass

    def fetch_job_group(self) -> Job_group:
        return self.job_group
    




    