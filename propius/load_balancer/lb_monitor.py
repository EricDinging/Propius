from propius.util import get_time, Propius_logger, Monitor
import matplotlib.pyplot as plt
import asyncio
import os


class LB_monitor(Monitor):
    def __init__(self, sched_alg: str, logger: Propius_logger, plot: bool=False):
        super().__init__("Load balancer", logger, plot)
        self.sched_alg = sched_alg
        self.plot = plot

    async def request(self):
        self._request()

    def report(self):
        self._gen_report()
        if self.plot:
            fig = plt.gcf()
            self._plot_request()
            plot_file = f"./propius/monitor/plot/lb_{self.sched_alg}.jpg"
            os.makedirs(os.path.dirname(plot_file), exist_ok=True)
            fig.savefig(plot_file)
