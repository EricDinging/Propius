from propius.parameter_server.config import GLOBAL_CONFIG_FILE
from propius.parameter_server.job import Propius_ps_job
from propius.parameter_server.client import Propius_ps_client
from tests.util import init_ps, clean_up
import yaml
import pytest
import time
import torch


@pytest.fixture
def setup_and_teardown_for_stuff():
    process = []
    print("\nsetting up")
    init_ps(process)
    yield
    print("\ntearing down")
    clean_up(process)


def test_ps_put_get(setup_and_teardown_for_stuff):
    with open(GLOBAL_CONFIG_FILE, "r") as gconfig:
        gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)

        job = Propius_ps_job(gconfig, 0)
        client = Propius_ps_client(gconfig, 0)

        time.sleep(1)

        client.connect()
        code, _, _ = client.get(0, 0)
        assert code == 3

        job.put(0, 2, {}, [torch.zeros(2), torch.zeros(2, 3)])

        time.sleep(3)
        code, _, data = client.get(0, 0)

        assert code == 1
        assert torch.equal(data[0], torch.zeros(2))
        assert torch.equal(data[1], torch.zeros(2, 3))

        code, _, data = client.get(0, 1)
        assert code == 2

        job.put(1, 2, {}, [torch.ones(2), torch.ones(2, 3)])

        code, _, data = client.get(0, 1)
        assert code == 1
        assert torch.equal(data[0], torch.ones(2))
        assert torch.equal(data[1], torch.ones(2, 3))

        # cache eviction test
        time.sleep(4)

        code, _, data = client.get(0, 1)
        assert code == 1
        assert torch.equal(data[0], torch.ones(2))
        assert torch.equal(data[1], torch.ones(2, 3))

        code, _, data = client.get(0, 0)
        assert code == 3