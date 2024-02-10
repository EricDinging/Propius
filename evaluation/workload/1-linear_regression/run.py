from propius.parameter_server.config import GLOBAL_CONFIG_FILE
from propius.parameter_server.job import Propius_ps_job
from propius.parameter_server.client import Propius_ps_client
from propius.util import init, init_ps, clean_up
import yaml
import time
import torch
import matplotlib.pyplot as plt

client_num = 3
clients = [None for _ in range(3)]
job = None

def plot_cost(J_all, num_epochs):
    plt.xlabel("Epochs")
    plt.ylabel("Cost")
    plt.plot(num_epochs, J_all, "m", linewidth="5")
    plt.show()


class Client:
    def __init__(self, data):
        self.mu = []
        self.std = []
        self.data = data
        self._normalize()
        self.x = self.data[:, :-1]
        self.y = self.data[:, -1]

        self.weigths = None

    def _normalize(self):
        for i in range(0, self.data.shape[1] - 1):
            mean = torch.mean(self.data[:, i])
            std = torch.std(self.data[:, i])
            self.data[:, i] = (self.data[:, i] - mean) / std
            self.mu.append(mean)
            self.std.append(std)

    def _h(self, x, theta):
        return torch.matmul(x, theta)

    def _cost_function(self, x, y, weights):
        return ((self._h(x, weights) - y).T @ (self._h(x, weights) - y)) / (
            2 * y.shape[0]
        )
    
    def _gradient_descent(self, x, y, theta, learning_rate=0.1, num_epochs=10):
        m = x.shape[0]
        running_cost = []
        for _ in range(num_epochs):
            h_x = self._h(x, theta)
            d_cost = (1 / m) * (x.T @ (h_x - y))
            theta = theta - (learning_rate) * d_cost
            running_cost.append(self._cost_function(x, y, theta))

        return theta, running_cost


def main():
    process = []
    try:
        print("\nsetting up")
        init(process)
        init_ps(process)

    except Exception as e:
        print(e)
    finally:
        print("\ntearing down")
        clean_up(process)


if __name__ == "__main__":
    main()
