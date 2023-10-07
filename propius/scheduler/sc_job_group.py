"""Scheduler job group manager"""

from propius.util.commons import Job_group
from propius.scheduler.sc_db_portal import SC_job_db_portal, SC_client_db_portal

class SC_job_group_manager:
    def __init__(self, 
                 job_db_portal: SC_job_db_portal, 
                 client_db_portal: SC_client_db_portal,
                 public_constraint_name: list):
        self.job_group = Job_group()
        self.job_db_portal = job_db_portal
        self.client_db_portal = client_db_portal
        self.public_constraint_name = public_constraint_name

    def update_job_group(self, job_id: int) -> bool:

        constraints_client_map = {}
        # Get constraints
        constraints = self.job_db_portal.get_job_constraints(job_id)
        if not constraints:
            return False
        # Clear past job group info
        self.job_group.clear_group_info()
        # Insert cst to job group
        self.job_group.insert_cst(constraints)

        for cst in self.job_group.constraint_list:
            # iterate over constraint, get updated and sorted job list
            if not self.job_db_portal.get_job_list(
                cst, self.job_group.cst_job_group_map[cst]
            ):
                self.job_group.remove_cst(cst)
        
        # search elig client size for each group
        for cst in self.job_group.constraint_list:
            constraints_client_map[cst] = self.client_db_portal.\
                get_client_proportion(cst)
            
        self.job_group.constraint_list.sort(key=lambda x: constraints_client_map[x])

        # Update group query
        bq = ""
        for cst in self.job_group.constraint_list:
            this_q = ""
            for idx, name in enumerate(self.public_constraint_name):
                this_q += f"@{name}: [{cst[idx]}, {self.public_max[name]}] "

            q = this_q + bq
            self.job_group[cst].insert_condition_and(q)
            bq = bq + f" -{this_q}"
        

    def fetch_job_group(self) -> Job_group:
        return self.job_group
    




    