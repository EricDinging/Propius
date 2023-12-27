import subprocess
from propius_controller.scheduler.sc_db_portal import SC_job_db_portal
from propius_controller.config import GLOBAL_CONFIG_FILE
from propius_controller.job.propius_job import Propius_job
from propius_controller.util import Msg_level, Propius_logger
from propius_controller.client.propius_client import Propius_client
import yaml
import time
import os
import signal
import atexit

process = []


def init():
    try:
        p = subprocess.Popen(
            ["docker", "compose", "-f", "compose_redis.yml", "up", "-d"]
        )
        process.append(p)

        p = subprocess.Popen(["python", "-m", "propius_controller.job_manager"])
        process.append(p)

        p = subprocess.Popen(["python", "-m", "propius_controller.scheduler"])
        process.append(p)

        p = subprocess.Popen(["python", "-m", "propius_controller.client_manager", "0"])
        process.append(p)

        p = subprocess.Popen(["python", "-m", "propius_controller.client_manager", "1"])
        process.append(p)

        p = subprocess.Popen(["python", "-m", "propius_controller.load_balancer"])
        process.append(p)

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def clean_up():
    for p in process:
        if p and p.poll() is None:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)


def job_request(gconfig, demand):
    jm_ip = gconfig["job_manager_ip"]
    jm_port = gconfig["job_manager_port"]

    job_config = {
        "public_constraint": {"cpu_f": 3, "ram": 3, "fp16_mem": 3, "android_os": 3},
        "private_constraint": {
            "dataset_size": 100,
        },
        "total_round": 10,
        "demand": demand,
        "job_manager_ip": jm_ip,
        "job_manager_port": jm_port,
        "ip": "localhost",
        "port": 6000,
    }
    propius_stub = Propius_job(job_config=job_config, verbose=True, logging=True)

    if not propius_stub.register():
        print(f"Parameter server: register failed")

    propius_stub.start_request()

    return propius_stub


def client_assign(gconfig, public_spec):
    lb_ip = gconfig["load_balancer_ip"]
    lb_port = gconfig["load_balancer_port"]
    client_config = {
        "public_specifications": public_spec,
        "private_specifications": {
            "dataset_size": 1000,
        },
        "load_balancer_ip": lb_ip,
        "load_balancer_port": lb_port,
        "option": 0.0,
    }

    propius_client = Propius_client(client_config=client_config, verbose=True)
    propius_client.connect()
    return propius_client.auto_assign()


def test_client_check_in():
    init()
    atexit.register(clean_up)
    with open(GLOBAL_CONFIG_FILE, "r") as gconfig:
        gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)
        logger = Propius_logger(log_file=None, verbose=True, use_logging=False)
        job_db = SC_job_db_portal(gconfig, logger)

        sched_alg = gconfig["sched_alg"]

        time.sleep(1)
        propius_job = job_request(gconfig, 1)
        time.sleep(1)
        result = client_assign(
            gconfig, {"cpu_f": 4, "ram": 5, "fp16_mem": 6, "android_os": 7}
        )
        assert result[1]
        assert result[2] == 0
        assert result[3] == "localhost"
        assert result[4] == 6000

        amount = job_db.get_field(0, "amount")
        demand = job_db.get_field(0, "demand")
        assert amount == demand
        assert amount == 1

        result = client_assign(
            gconfig, {"cpu_f": 4, "ram": 5, "fp16_mem": 6, "android_os": 7}
        )
        assert not result[1]
        assert result[2] == -1

        propius_job.start_request()
        time.sleep(1)
        result = client_assign(
            gconfig, {"cpu_f": 4, "ram": 5, "fp16_mem": 6, "android_os": 7}
        )
        assert result[1]
        assert result[2] == 0
        assert result[3] == "localhost"
        assert result[4] == 6000
