from propius_parameter_server.config import GLOBAL_CONFIG_FILE
from propius_parameter_server.job import Propius_ps_job
from propius_parameter_server.client import Propius_ps_client
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
        job.connect()
        client.connect()
        code, _, _ = client.get(0, 0)
        assert code == 3

        job.put(0, 2, {}, [torch.zeros(2), torch.zeros(2, 3)])

        time.sleep(3)
        code, _, data = client.get(0, 0)
        assert code == 1

        assert torch.equal(data[0], torch.zeros(2))
        assert torch.equal(data[1], torch.zeros(2, 3))

        data[0] += 1
        data[1] += 1
        code = client.push(0, 1, data)
        assert code == 4
        code = client.push(0, 0, data)
        assert code == 1

        code, _, _ = job.get(0)
        assert code == 6

        code, _, data = client.get(0, 0)
        data[0] += 2
        data[1] += 2
        code = client.push(0, 0, data)
        assert code == 1

        code, _, data = job.get(0)
        assert code == 1
        assert torch.equal(data[0], torch.zeros(2) + 3)
        assert torch.equal(data[1], torch.zeros(2, 3) + 3)

        code, _, data = client.get(0, 0)
        data[0] += 1
        data[1] += 1
        code = client.push(0, 0, data)
        assert code == 1

        time.sleep(2)
        code, _, data = job.get(0)
        assert code == 1
        assert torch.equal(data[0], torch.zeros(2) + 4)
        assert torch.equal(data[1], torch.zeros(2, 3) + 4)

        data[0] /= 2
        data[1] /= 2
        job.put(1, 1, {}, data)
        code, _, _ = client.get(0, 0)
        assert code == 3

        time.sleep(1)
        code, _, _ = client.get(0, 4)
        assert code == 2

        code, _, new_data = client.get(0, 1)
        assert code == 1
        assert torch.equal(data[0], new_data[0])
        assert torch.equal(data[1], new_data[1])

        job.delete()
        code, _, _ = client.get(0, 1)
        assert code == 3
