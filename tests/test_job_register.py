import subprocess
from propius_controller.database.db import Job_db
from propius_controller.config import GLOBAL_CONFIG_FILE
from propius_controller.job.propius_job_aio import Propius_job
from propius_controller.util import Msg_level, Propius_logger
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

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def clean_up():
    for p in process:
        if p and p.poll() is None:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)


def job_register(gconfig):
    jm_ip = gconfig["job_manager_ip"]
    jm_port = gconfig["job_manager_port"]

    job_config = {
        "public_constraint": {"cpu_f": 0, "ram": 0, "fp16_mem": 0, "android_os": 0},
        "private_constraint": {
            "dataset_size": 100,
        },
        "total_round": 10,
        "demand": 5,
        "job_manager_ip": jm_ip,
        "job_manager_port": jm_port,
        "ip": "localhost",
        "port": 6000,
    }
    propius_stub = Propius_job(job_config=job_config, verbose=True, logging=True)

    if not propius_stub.register():
        print(f"Parameter server: register failed")


def test_register():
    init()
    atexit.register(clean_up)
    with open(GLOBAL_CONFIG_FILE, "r") as gconfig:
        gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)
        logger = Propius_logger(log_file=None, verbose=True, use_logging=False)
        job_db = Job_db(gconfig, False, logger)

        time.sleep(1)
        job_register(gconfig)
        assert job_db.get_job_size() == 1

        time.sleep(1)
        job_register(gconfig)

        assert job_db.get_job_size() == 2
