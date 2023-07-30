import subprocess
import yaml
import time

with open('./global_config.yml', 'r') as gyamlfile:
    gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
    ip = gconfig['job_driver_ip']
    port = int(gconfig['job_driver_starting_port'])

    with open("./propius/job_sim/job_trace.txt", "r") as file:
        i = 0
        for line in file:
            line = line.strip().split(" ")
            time.sleep(int(line[0]))
            command = ["python", "./propius/job_sim/job.py", f"./propius/job_sim/profile/job_{line[1]}.yml", 
                       f"{line[2]}", f"{ip}", f"{port + i}"]
            print(command)
            subprocess.Popen(command)
            i += 1