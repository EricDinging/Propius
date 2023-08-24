from propius.util.monitor import *
from propius.util.commons import *
import asyncio
import os


class LB_monitor(Monitor):
    def __init__(self, sched_alg: str, plot: bool=False):
        super().__init__("Load balancer", plot)
        self.sched_alg = sched_alg
        self.lock = asyncio.Lock()
        self.plot = plot

    async def request(self):
        async with self.lock:
            self._request()

    def report(self):
        self._gen_report()
        if self.plot:
            fig = plt.gcf()
            self._plot_request()
            fig.savefig(f"./propius/load_balancer/LB-{self.sched_alg}-{get_time()}")
