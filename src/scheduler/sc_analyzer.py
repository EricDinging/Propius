import sys
sys.path.append('..')

from src.util.analyzer import *
import asyncio
import time

class SC_analyzer(Analyzer):
    def __init__(self, sched_alg:str, total_running_time:int):
        super().__init__("Scheduler", total_running_time)
        self.job_size_latency_map = {}
        self.job_request_map = {}
        self.lock = asyncio.Lock()
        self.sched_alg = sched_alg

    async def request_start(self, job_id:int):
        async with self.lock:
            self._request()
            self.job_request_map[job_id] = time.time()
    
    async def request_end(self, job_id:int, job_size:int):
        async with self.lock:
            runtime = time.time() - self.job_request_map[job_id]
            if job_size not in self.job_size_latency_map:
                self.job_size_latency_map[job_size] = [runtime]
            else:
                self.job_size_latency_map[job_size].append(runtime)
            del self.job_request_map[job_id]

    def _plot_time(self):
        lists = sorted(self.job_size_latency_map.items())
        x, y = zip(*lists)
        plt.scatter(x, y)
        plt.title('Scheduling Alg latency')
        plt.xlabel('Number of jobs')
        plt.ylabel('Latency (sec)')

    def report(self):
        for size, latency_list in self.job_size_latency_map.items():
            self.job_size_latency_map[size] = sum(latency_list) / len(latency_list)

        lists = sorted(self.job_size_latency_map.items())
        x, y = zip(*lists)

        str1 = self._gen_report()
        with open(f'./log/SC-{self.sched_alg}-{int(time.time())}.txt', 'w') as file:
            file.write(str1)
            file.write("\n")
            for idx, job_size in enumerate(x):
                file.write(f"Job size: {job_size}, latency: {y[idx]}\n")

        fig = plt.gcf()
        plt.subplot(2, 1, 1)
        self._plot_time()
        plt.subplot(2, 1, 2)
        self._plot_request()
        plt.tight_layout()
        plt.show()
        fig.savefig(f"./fig/SC-{self.sched_alg}-{int(time.time())}")


