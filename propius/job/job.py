from propius.controller.job.propius_job import Propius_job
from propius.parameter_server.job.propius_ps import Propius_ps_job
import time


class Job:
    def __init__(self, config: dict, verbose: bool = False, logging: bool = False):
        self.job_controller = Propius_job(config, verbose, logging)

        self.id = -1
        self.job_ps = None
        self.config = config
        self.verbose = verbose
        self.logging = logging

        self.total_round = config["total_round"]
        self.demand = config["demand"]

        self.round = 0

    def register(self) -> bool:
        if self.job_controller.register():
            self.id = self.job_controller.id

            self.job_ps = Propius_ps_job(
                self.config, self.id, self.verbose, self.logging
            )
            return True
        else:
            return False

    def request(self, meta: dict, data: list, demand: int = -1) -> bool:
        new_demand = demand > 0
        this_round_demand = self.demand if not new_demand else demand

        this_round = self.job_controller.start_request(new_demand, this_round_demand)
        self.round = this_round
        if this_round != -1:
            if self.job_ps.put(this_round, this_round_demand, meta, data) == 1:
                return True
        return False

    def reduce(self, timeout: float = 60):
        if self.round == -1:
            return None
        
        start_time = time.time()
        while True:
            code, meta, data = self.job_ps.get(self.round)
            if code == 1:
                self.job_controller.end_request()

                return (meta, data)

            elif code == 3:
                raise RuntimeError("error code 3 from parameter server")

            if time.time() - start_time >= timeout:
                break
            time.sleep(5)

        return None

    def complete(self):
        self.job_controller.complete_job()
        self.job_ps.delete()
