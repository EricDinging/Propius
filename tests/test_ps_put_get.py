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
        client.connect()
        code, _, _ = client.get(0, 0)
        assert code == 3

        job.put(0, 2, {}, "HELLO WORLD")

        time.sleep(3)
        code, _, data = client.get(0, 0)
        assert code == 1
        assert data == "HELLO WORLD"

        code = client.push(0, 1, "HELLO WORLD HELLO WOLRD")
        assert code == 4
        code = client.push(0, 0, "HELLO WORLD HELLO WOLRD")
        assert code == 1

        code, _, _ = job.get(0)
        assert code == 6

        code = client.push(0, 0, "HELLO WORLD HELLO WOLRD HELLO WOLRD")
        assert code == 1

        code, _, data = job.get(0)
        assert code == 1
        assert data == "HELLO WORLD HELLO WOLRD HELLO WOLRD"

        code = client.push(0, 0, "HELLO WORLD HELLO WOLRD HELLO WOLRD HELLO WORLD")
        assert code == 1

        time.sleep(2)
        code, _, data = job.get(0)
        assert code == 1
        assert data == "HELLO WORLD HELLO WOLRD HELLO WOLRD HELLO WORLD"

        job.put(1, 1, {}, "HELLO")
        code, _, _ = client.get(0, 0)
        assert code == 3

        time.sleep(1)
        code, _, _ = client.get(0, 4)
        assert code == 2

        code, _, _ = client.get(0, 1)
        assert code == 1

        job.delete()
        code, _, _ = client.get(0, 1)
        assert code == 3
