import subprocess
import yaml
import time

with open('./evaluation/evaluation_config.yml', 'r') as gyamlfile:
    config = yaml.load(gyamlfile, Loader=yaml.FullLoader)
    ip = config['job_driver_ip']
    port = int(config['job_driver_starting_port'])
    num = config['total_job']

    with open(f"./evaluation/job/job_trace_{num}.txt", "r") as file:
        i = 0

        for line in file:
            line = line.strip().split(" ")
            time.sleep(int(line[0]))
            command = [
                "python",
                "./evaluation/job/parameter_server.py",
                f"./evaluation/job/profile/job_{line[1]}.yml",
                f"{ip}",
                f"{port + i}"]
            print(command)
            subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            i += 1