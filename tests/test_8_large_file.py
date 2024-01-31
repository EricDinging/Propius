from propius.parameter_server.config import GLOBAL_CONFIG_FILE
from propius.parameter_server.job import Propius_ps_job
from propius.parameter_server.client import Propius_ps_client
from tests.util import init_ps, clean_up
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


def test_large_file(setup_and_teardown_for_stuff):
    with open(GLOBAL_CONFIG_FILE, "r") as gconfig:
        gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)

        job = Propius_ps_job(gconfig, 0)
        client = Propius_ps_client(gconfig, 0, verbose=True)

        time.sleep(1)

        model = models.vgg16(weights="IMAGENET1K_V1")
        model_weights = []
        for param in model.parameters():
            model_weights.append(param)

        job.put(0, 2, {}, model_weights)
        time.sleep(3)
        code, _, data = client.get(0, 0)

        assert code == 1
        for param_c, param_s in zip(data, model_weights):
            assert torch.equal(param_c, param_s)

        # calculate update
        updates = []
        for param in data:
            updates.append(param * 0.1)

        client.push(0, 0, updates)

        code, _, data = job.get(0)
        assert code == 6

        code, _, data = client.get(0, 0)
        assert code == 1

        # calculate update
        updates_2 = []
        for param in data:
            updates_2.append(param * 0.2)

        client.push(0, 0, updates_2)

        time.sleep(gconfig["leaf_aggregation_store_ttl"] + 3)
        code, _, result = job.get(0)
        assert code == 1

        for param_result, param_s in zip(result, model_weights):
            assert np.allclose(
                param_result.detach().numpy(), param_s.detach().numpy() * 0.3,
                atol=1e-7
            )
        code, _, data = client.get(0, 1)
        assert code == 2

        job.delete()
        time.sleep(gconfig["leaf_parameter_store_ttl"] + 1)
        code, _, data = client.get(0, 0)
        assert code == 3
