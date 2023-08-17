from propius.util.commons import *
from propius.util.monitor import *
import time
import asyncio
import sys
import os


class SC_monitor(Monitor):
    def __init__(self, sched_alg: str):
        super().__init__("Scheduler")
        self.job_size_latency_map = {}
        self.job_request_map = {}
        self.lock = asyncio.Lock()
        self.sched_alg = sched_alg

        fig_dir = "./propius/fig"
        log_dir = "./propius/log"

        if not os.path.exists(fig_dir):
            os.mkdir(fig_dir)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

    async def request_start(self, job_id: int):
        async with self.lock:
            self._request()
            self.job_request_map[job_id] = time.time()

    async def request_end(self, job_id: int, job_size: int):
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
            self.job_size_latency_map[size] = sum(
                latency_list) / len(latency_list)

        lists = sorted(self.job_size_latency_map.items())
        if len(lists) > 0:
            x, y = zip(*lists)
            str1 = self._gen_report()
            with open(f'./propius/log/SC-{self.sched_alg}-{get_time()}.txt', 'w') as file:
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
            fig.savefig(f"./propius/fig/SC-{self.sched_alg}-{get_time()}")
