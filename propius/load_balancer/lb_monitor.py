from propius.util.monitor import *
from propius.util.commons import *
import asyncio
import os


class LB_monitor(Monitor):
    def __init__(self, sched_alg: str):
        super().__init__("Load balancer")
        self.sched_alg = sched_alg
        self.lock = asyncio.Lock()

        fig_dir = "./propius/fig"
        log_dir = "./propius/log"

        if not os.path.exists(fig_dir):
            os.mkdir(fig_dir)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

    async def request(self):
        async with self.lock:
            self._request()

    def report(self):
        str1 = self._gen_report()
        with open(f'./propius/log/LB-{self.sched_alg}-{get_time()}.txt', 'w') as file:
            file.write(str1)
            file.write("\n")

        fig = plt.gcf()
        self._plot_request()
        plt.show()
        fig.savefig(f"./propius/fig/LB-{self.sched_alg}-{get_time()}")
