from propius.util.analyzer import *
import asyncio

class CM_analyzer(Analyzer):
    def __init__(self, sched_alg:str, total_running_time:int):
        super().__init__("Client manager", total_running_time)
        self.sched_alg = sched_alg
        self.lock = asyncio.Lock()
        self.total_client_num = 0
        self.total_success_num = 0
        self.total_client_not_elig_num = 0
        self.total_client_over_assign_num = 0

    async def client_checkin(self, is_elig:bool, job_size:int):
        async with self.lock:
            self._request()
            self.total_client_num += 1
            if not is_elig and job_size > 0:
                self.total_client_not_elig_num += 1
    
    async def client_accept(self, success:bool):
        async with self.lock:
            self._request()
            if not success:
                self.total_client_over_assign_num += 1
            else:
                self.total_success_num += 1

    def report(self):
        if self.total_client_num > 0:
            str1 = self._gen_report()
            util_rate = self.total_success_num / (self.total_success_num + self.total_client_not_elig_num + self.total_client_over_assign_num)

            str2 = f"Client manager: client num: {self.total_client_num}, util rate: {util_rate:.3f}, not elig num: {self.total_client_not_elig_num}, over-assign num: {self.total_client_over_assign_num}"

            with open(f'./log/CM-{self.sched_alg}-{int(time.time())}.txt', 'w') as file:
                file.write(str1)
                file.write("\n")
                file.write(str2)
                file.write("\n")

            fig = plt.gcf()
            self._plot_request()
            plt.show()
            fig.savefig(f"./fig/CM-{self.sched_alg}-{int(time.time())}")