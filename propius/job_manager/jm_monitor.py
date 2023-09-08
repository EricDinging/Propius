import asyncio
import time
import matplotlib.pyplot as plt
from propius.util.monitor import Monitor
from propius.util.commons import Msg_level, My_logger, get_time
import os

class JM_monitor(Monitor):
    def __init__(self, sched_alg: str, logger: My_logger, plot: bool=False):
        super().__init__("Job manager", logger, plot)
        self.lock = asyncio.Lock()
        self.sched_alg = sched_alg

        self.total_job = 0

        self.start_time = int(time.time())
        self.job_time_num = [0]
        self.job_timestamp = [0]

        self.constraint_jct_dict = {}
        self.constraint_sched_dict = {}
        self.constraint_cnt = {}
        self.plot = plot

    async def job_register(self):
        async with self.lock:
            self.total_job += 1
            if self.plot:
                runtime = int(time.time()) - self.start_time
                self.job_timestamp.append(runtime)
                self.job_timestamp.append(self.job_timestamp[-1])
                self.job_time_num.append(self.job_time_num[-1])
                self.job_time_num.append(self.job_time_num[-1] + 1)

    async def job_finish(self, constraint: tuple,
                         demand: int, total_round: int, job_runtime: float, sched_latency: float):
        async with self.lock:
            runtime = int(time.time()) - self.start_time
            self.job_timestamp.append(runtime)
            self.job_timestamp.append(self.job_timestamp[-1])
            self.job_time_num.append(self.job_time_num[-1])
            self.job_time_num.append(self.job_time_num[-1] - 1)

            key = (constraint, demand, total_round)
            if key not in self.constraint_jct_dict:
                self.constraint_jct_dict[key] = 0
                self.constraint_sched_dict[key] = 0
                self.constraint_cnt[key] = 0
            self.constraint_jct_dict[key] += job_runtime
            self.constraint_cnt[key] += 1                
            self.constraint_sched_dict[key] += sched_latency

    async def request(self):
        async with self.lock:
            self._request()

    def _plot_job(self):
        plt.plot(self.job_timestamp, self.job_time_num)
        plt.title('Job trace')
        plt.ylabel('Number of jobs')
        plt.xlabel('Time (sec)')

    def report(self):
        self._gen_report()
        self.logger.print(f"Job manager: total job: {self.total_job}", Msg_level.INFO)


        for constraint, sum_jct in self.constraint_jct_dict.items():
            cnt = self.constraint_cnt[constraint]
            avg_jct = sum_jct / cnt
            sum_sched = self.constraint_sched_dict[constraint]
            avg_sched = sum_sched / cnt

            self.logger.print(
                f"Job group: {constraint}, num: {cnt}, avg JCT: {avg_jct:.3f}, avg sched latency: {avg_sched:.3f}\n")
        
        if self.plot:
            fig = plt.gcf()
            plt.subplot(2, 1, 1)
            self._plot_job()
            plt.subplot(2, 1, 2)
            self._plot_request()
            plt.tight_layout()

            plot_file = f"./propius/monitor/plot/jm_{self.sched_alg}_{get_time()}.jpg"
            os.makedirs(os.path.dirname(plot_file), exist_ok=True)
            fig.savefig(plot_file)

