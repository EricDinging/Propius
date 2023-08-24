import time
import matplotlib.pyplot as plt
from propius.util.commons import *

class Monitor:
    def __init__(self, server_name: str, plot: bool = False):
        self.start_time = int(time.time())
        self.plot = plot
        self.request_num_log = {}
        self.request_num = 0
        self.server_name = server_name

    def _request(self):
        """Log request for analysis
        """
        self.request_num += 1

        if self.plot:
            runtime = int(time.time()) - self.start_time
            if runtime % 60 == 0:
                if runtime not in self.request_num_log:
                    self.request_num_log[runtime] = 0
                self.request_num_log[runtime] += 1

    def _plot_request(self):
        if self.plot:
            keys = self.request_num_log.keys()
            values = self.request_num_log.values()

            plt.scatter(keys, values)
            plt.title(self.server_name + ' load')
            plt.ylabel('Number of requests')
            plt.xlabel('Time (sec)')

    def _gen_report(self):
        runtime = int(time.time()) - self.start_time
        avg_request_per_second = self.request_num / runtime

        if self.plot:
            max_request_per_second = max(self.request_num_log.values())
            report = self.server_name + \
                f": avg request per second: {avg_request_per_second:.3f}, max request per second sampled: {max_request_per_second}"
        else:
            report = self.server_name + \
                f": avg request per second: {avg_request_per_second:.3f}"
        
        custom_print(report, INFO)
