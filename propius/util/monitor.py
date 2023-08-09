import time
import matplotlib.pyplot as plt


class Monitor:
    def __init__(self, server_name: str):
        self.start_time = int(time.time())
        self.request_num_log = {}
        self.server_name = server_name

    def _request(self):
        """Log request for analysis
        """
        runtime = int(time.time()) - self.start_time
        if runtime not in self.request_num_log:
            self.request_num_log[runtime] = 0
        self.request_num_log[runtime] += 1

    def _plot_request(self):
        keys = self.request_num_log.keys()
        values = self.request_num_log.values()
        plt.plot(keys, values)
        plt.title(self.server_name + ' load')
        plt.ylabel('Number of requests')
        plt.xlabel('Time (sec)')

    def _gen_report(self) -> str:
        report = ""
        if len(self.request_num_log) > 0:
            runtime = int(time.time()) - self.start_time
            avg_request_per_second = sum(self.request_num_log.values()) / runtime
            max_request_per_second = max(self.request_num_log.values())
            report = self.server_name + \
                f": avg request per second: {avg_request_per_second:.3f}, max request per second: {max_request_per_second}"
        return report
