import subprocess
import yaml
import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time


with open('./global_config.yml', 'r') as gyamlfile:
    gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
    ip = gconfig['job_driver_ip']
    port = int(gconfig['job_driver_starting_port'])

    job_start_num = int(gconfig['total_job'])
    job_profile_num = int(gconfig['job_profile_num'])

    for i in range(job_start_num):
        command = ["python", "./src/job/job.py", f"./src/job/profile/job_{i % job_profile_num}.yml", 
                    f"{i}", f"{ip}", f"{port}"]
        print(command)
        subprocess.Popen(command)
        port += 1

            