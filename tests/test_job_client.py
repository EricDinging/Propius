import subprocess
import threading
import os

process_list = []
PROPIUS_HOME = os.environ["PROPIUS_HOME"]

def set_up():
    print("---Setting environment for job client testing---")
    clean_script = f'{PROPIUS_HOME}/scripts/clean.sh'
    subprocess.run(["sh", clean_script], check=True)
    print("---Shell script executed successfully---")

    config_script = f'{PROPIUS_HOME}/tests/test_config.py'
    subprocess.run(["python", config_script], check=True)
    print("---Config script executed successfully---")

    command = [
        "docker",
        "compose",
        "-f",
        f"{PROPIUS_HOME}/compose_propius.yml",
        "up",
    ]
    p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
    process_list.append(p)

set_up()

for process in process_list:
    process.wait()

print("---All processes have completed or timed out---")