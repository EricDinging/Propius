from propius.util.analyzer import *
import asyncio

class LB_analyzer(Analyzer):
    def __init__(self, sched_alg:str, total_running_time:int):
        super().__init__("Load balancer", total_running_time)
        self.sched_alg = sched_alg
        self.lock = asyncio.Lock()

    async def request(self):
        async with self.lock:
            self._request()

    def report(self):
        str1 = self._gen_report()
        with open(f'./log/LB-{self.sched_alg}-{int(time.time())}.txt', 'w') as file:
            file.write(str1)
            file.write("\n")

        fig = plt.gcf()
        self._plot_request()
        plt.show()
        fig.savefig(f"./fig/LB-{self.sched_alg}-{int(time.time())}")
