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
