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


def init(process):
    try:
        p = subprocess.Popen(
            ["docker", "compose", "-f", "compose_redis.yml", "up", "-d"]
        )
        process.append(p.pid)

        p = subprocess.Popen(["python", "-m", "propius_controller.job_manager"])
        process.append(p.pid)

        p = subprocess.Popen(["python", "-m", "propius_controller.scheduler"])
        process.append(p.pid)

        p = subprocess.Popen(["python", "-m", "propius_controller.client_manager", "0"])
        process.append(p.pid)

        p = subprocess.Popen(["python", "-m", "propius_controller.client_manager", "1"])
        process.append(p.pid)

        p = subprocess.Popen(["python", "-m", "propius_controller.load_balancer"])
        process.append(p.pid)

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def clean_up(process):
    for p in process:
        try:
            os.kill(p, signal.SIGTERM)
        except Exception as e:
            print(e)
            
