from propius_parameter_server.config import GLOBAL_CONFIG_FILE
from propius_parameter_server.job import Propius_ps_job
from propius_parameter_server.client import Propius_ps_client
from tests.util import init_ps, clean_up
import yaml
import pytest
import time


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
        job.put(0, 0, "", "HELLO WORLD")

        time.sleep(3)
        client.connect()
        code, meta, data = client.get(0, 0)
        assert code == 1
        assert data == "HELLO WORLD"

        time.sleep(1)

        job.put(0, 1, "", "HELLO")
        code, _, _ = client.get(0, 0)
        assert code == 3

        time.sleep(1)
        code, _, _ = client.get(0, 4)
        assert code == 2
