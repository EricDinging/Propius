from propius.parameter_server.config import GLOBAL_CONFIG_FILE
from propius.parameter_server.job import Propius_ps_job
from propius.parameter_server.client import Propius_ps_client
from propius.util import init_ps, clean_up
import yaml
import pytest
import time
import torch
import numpy as np
import torchvision.models as models


@pytest.fixture
def setup_and_teardown_for_stuff():
    process = []
    print("\nsetting up")
    init_ps(process)
    yield
    print("\ntearing down")
    clean_up(process)


def test_measurement(setup_and_teardown_for_stuff):
    with open(GLOBAL_CONFIG_FILE, "r") as gconfig:
        gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)

        job = Propius_ps_job(gconfig, 0)
        client = Propius_ps_client(gconfig, 0, verbose=True)

        time.sleep(1)

        model = models.vgg16(weights="IMAGENET1K_V1")
        model_weights = []
        for param in model.parameters():
            model_weights.append(param)

        job.put(0, 4, {}, model_weights)
        time.sleep(3)

        print("===Client GET CACHE MISS")
        print("===Leaf GET")
        code, _, data = client.get(0, 0)

        time.sleep(5)
        print("===Client GET CACHE HIT")
        code, _, data = client.get(0, 0)

        updates = []
        for param in data:
            updates.append(param * 0.1)

        print("===Client PUSH new")
        client.push(0, 0, updates)
        print("===Client PUSH agg")
        client.push(0, 0, updates)
        print("===Leaf PUSH new")
        time.sleep(gconfig["leaf_aggregation_store_ttl"] + 3)

        print("===Client PUSH new")
        client.push(0, 0, updates)
        print("===Client PUSH agg")
        client.push(0, 0, updates)
        print("===Leaf PUSH agg")
        time.sleep(gconfig["leaf_aggregation_store_ttl"] + 3)

        code, _, result = job.get(0)
        assert code == 1
