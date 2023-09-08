import asyncio
from propius.util.monitor import Monitor
from propius.util.commons import Msg_level, My_logger, get_time
import os
import matplotlib.pyplot as plt

class CM_monitor(Monitor):
    def __init__(self, sched_alg: str, logger: My_logger, plot: bool=False):
        super().__init__("Client manager", logger, plot)
        self.sched_alg = sched_alg
        self.lock = asyncio.Lock()
        self.client_check_in_num = 0
        self.client_ping_num = 0
        self.client_accept_num = 0
        self.client_over_assign_num = 0
        self.plot = plot

    async def client_checkin(self):
        async with self.lock:
            self._request()
            self.client_check_in_num += 1

    async def client_ping(self):
        async with self.lock:
            self._request()
            self.client_ping_num += 1

    async def client_accept(self, success: bool):
        async with self.lock:
            self._request()
            if success:
                self.client_accept_num += 1
            else:
                self.client_over_assign_num += 1

    def report(self, id: int):
        self._gen_report()

        self.logger.print(f"Client manager {id}: check in {self.client_check_in_num}, ping {self.client_ping_num}, "
        f"accept {self.client_accept_num}, over-assign {self.client_over_assign_num}", Msg_level.INFO)

        if self.plot:
            fig = plt.gcf()
            self._plot_request()
            plot_file = f"./propius/monitor/plot/cm_{id}_{self.sched_alg}_{get_time()}.jpg"
            os.makedirs(os.path.dirname(plot_file), exist_ok=True)
            fig.savefig(plot_file)
