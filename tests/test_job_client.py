import subprocess

command = [
    "docker",
    "compose",
    "-f",
    "./compose_redis.yml",
    "up",
]

process_list = []

p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)
process_list.append(p)


for p in process_list:
    p.wait()