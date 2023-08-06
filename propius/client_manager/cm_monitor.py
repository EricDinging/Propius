import asyncio
from propius.util.monitor import *
from propius.util.commons import *

class CM_monitor(Monitor):
    def __init__(self, sched_alg:str):
        super().__init__("Client manager")
        self.sched_alg = sched_alg
        self.lock = asyncio.Lock()
        self.total_client_num = 0

    async def client_checkin(self):
        async with self.lock:
            self._request()
            self.total_client_num += 1
    
    async def client_ping(self):
        async with self.lock:
            self._request()
    
    async def client_accept(self, success:bool):
        async with self.lock:
            self._request()

    def report(self, id:int):
        if self.total_client_num > 0:
            str1 = self._gen_report()

            str2 = f"Client manager {id}: client num: {self.total_client_num}"

            with open(f'./log/CM{id}-{self.sched_alg}-{get_time()}.txt', 'w') as file:
                file.write(str1)
                file.write("\n")
                file.write(str2)
                file.write("\n")

            fig = plt.gcf()
            self._plot_request()
            plt.show()
            fig.savefig(f"./fig/CM{id}-{self.sched_alg}-{get_time()}")