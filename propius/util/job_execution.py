from propius.job import Job as job_portal
import torch


class Job:
    def __init__(self, model, config):
        self.model = model

        self.config = config
        self.job_portal = job_portal(config, True, False)

    def register(self):
        self.job_portal.register()

    def request(self):
        weights = self.model["weights"]
        self.job_portal.request({}, data=[weights])

    def update(self):
        _, aggregation = self.job_portal.reduce()
        new_weights = aggregation[0]

        num_client = self.config["demand"]
        self.model["weights"] = new_weights / num_client

    def complete(self):
        self.job_portal.complete()

