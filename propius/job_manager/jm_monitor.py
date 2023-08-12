import asyncio
import time
from propius.util.monitor import *
from propius.util.commons import *
import os


class JM_monitor(Monitor):
    def __init__(self, sched_alg: str):
        super().__init__("Job manager")
        self.lock = asyncio.Lock()
        self.sched_alg = sched_alg

        self.total_job = 0
        self.total_round = 0

        self.start_time = int(time.time())
        self.job_time_num = [0]
        self.job_timestamp = [0]

        self.constraint_jct_dict = {}
        self.constraint_sched_dict = {}

        fig_dir = "./propius/fig"
        log_dir = "./propius/log"

        if not os.path.exists(fig_dir):
            os.mkdir(fig_dir)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

    async def job_register(self):
        async with self.lock:
            self.total_job += 1

            runtime = int(time.time()) - self.start_time
            self.job_timestamp.append(runtime)
            self.job_timestamp.append(self.job_timestamp[-1])
            self.job_time_num.append(self.job_time_num[-1])
            self.job_time_num.append(self.job_time_num[-1] + 1)

    async def job_request(self):
        async with self.lock:
            self.total_round += 1

    async def job_finish(self, constraint: tuple,
                         demand: int, total_round: int, job_runtime: float, sched_latency: float):
        async with self.lock:
            runtime = int(time.time()) - self.start_time
            self.job_timestamp.append(runtime)
            self.job_timestamp.append(self.job_timestamp[-1])
            self.job_time_num.append(self.job_time_num[-1])
            self.job_time_num.append(self.job_time_num[-1] - 1)

            key = (constraint, demand, total_round)
            if key in self.constraint_jct_dict:
                self.constraint_jct_dict[key].append(job_runtime)
            else:
                self.constraint_jct_dict[key] = [job_runtime]

            if key in self.constraint_sched_dict:
                self.constraint_sched_dict[key].append(sched_latency)
            else:
                self.constraint_sched_dict[key] = [sched_latency]

    async def request(self):
        async with self.lock:
            self._request()

    def _plot_job(self):
        plt.plot(self.job_timestamp, self.job_time_num)
        plt.title('Job trace')
        plt.ylabel('Number of jobs')
        plt.xlabel('Time (sec)')

    def report(self):
        str1 = self._gen_report()

        with open(f'./propius/log/JM-{self.sched_alg}-{get_time()}.txt', 'w') as file:
            file.write(str1)
            file.write("\n")
            file.write(
                f"Job manager: total job: {self.total_job}, total round: {self.total_round}\n")

            total_sum_jct = 0
            total_sum_sched_latency = 0
            total_num = 0
            for constraint, jct in self.constraint_jct_dict.items():
                if len(jct) > 0:
                    sum_jct = sum(jct)
                    total_sum_jct += sum_jct
                    avg_jct = sum_jct / len(jct)
                    total_num += len(jct)

                    sum_sched = sum(self.constraint_sched_dict[constraint])
                    total_sum_sched_latency += sum_sched
                    avg_sched = sum_sched / len(jct)
                    file.write(
                        f"Job group: {constraint}, num: {len(jct)}, avg JCT: {avg_jct:.3f}, avg sched latency: {avg_sched:.3f}\n")
            if total_num > 0:
                file.write(
                    f"Total avg JCT: {total_sum_jct / total_num:.3f}, avg sched latency: {total_sum_sched_latency / total_num:.3f}\n")
        fig = plt.gcf()
        plt.subplot(2, 1, 1)
        self._plot_job()
        plt.subplot(2, 1, 2)
        self._plot_request()
        plt.tight_layout()
        plt.show()
        fig.savefig(f"./propius/fig/JM-{self.sched_alg}-{get_time()}")
