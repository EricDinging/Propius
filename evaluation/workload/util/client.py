from propius.client import Client as client_portal
import torch

class Client:
    def __init__(self, data, config):
        self.data = data
        self.mu = []
        self.std = []

        self._normalize()
        self.x = self.data[:, :-1]
        self.y = self.data[:, -1]

        self.weigths = None
        self.new_weights = None

        self.config = config
        self.client_portal = client_portal(config, True, True)

    def _normalize(self):
        for i in range(0, self.data.shape[1] - 1):
            mean = torch.mean(self.data[:, i])
            std = torch.std(self.data[:, i])
            self.data[:, i] = (self.data[:, i] - mean) / std
            self.mu.append(mean)
            self.std.append(std)

    def _h(self, x, weights):
        return torch.matmul(x, weights)

    def _cost_function(self, x, y, weights):
        return ((self._h(x, weights) - y).T @ (self._h(x, weights) - y)) / (
            2 * y.shape[0]
        )

    def _gradient_descent(self, x, y, weights, learning_rate=0.1, num_epochs=10):
        m = x.shape[0]
        running_cost = []
        for _ in range(num_epochs):
            h_x = self._h(x, weights)
            d_cost = (1 / m) * (x.T @ (h_x - y))
            weights = weights - (learning_rate) * d_cost
            running_cost.append(self._cost_function(x, y, weights))

        return weights, running_cost
    
    def get(self):
        result = self.client_portal.get()
        meta, self.weigths = result

    def execute(self):
        num_epochs = 10
        learning_rate = 0.1
        self.new_weights, _ = self._gradient_descent(self.x, self.y, self.weights, learning_rate, num_epochs)

    def push(self):
        if self.new_weights:
            self.client_portal.push(self.new_weights)
            self.new_weights = None

    
