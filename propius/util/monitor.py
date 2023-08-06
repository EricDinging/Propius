import time
import matplotlib.pyplot as plt

class Monitor:
    def __init__(self, server_name:str, total_running_time:int):
        self.start_time = int(time.time())
        self.total_running_time = total_running_time
        self.request_num_list = [0 for _ in range(total_running_time)]
        self.server_name = server_name

    def _request(self):
        runtime = int(time.time()) - self.start_time
        if runtime >= self.total_running_time:
            return
        self.request_num_list[runtime] += 1

    def _plot_request(self):
        plt.plot(self.request_num_list)
        plt.title(self.server_name + ' load')
        plt.ylabel('Number of requests')
        plt.xlabel('Time (sec)')

    def _gen_report(self)->str:
        runtime = int(time.time()) - self.start_time
        runtime = min(runtime, self.total_running_time)
        avg_request_per_second = sum(self.request_num_list) / runtime
        max_request_per_second = max(self.request_num_list)
        report = self.server_name + f": avg request per second: {avg_request_per_second:.3f}, max request per second: {max_request_per_second}"
        return report

    