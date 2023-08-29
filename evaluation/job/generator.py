import yaml
import random
import numpy as np
import os

random.seed(1)

# generate txt with format: time in minute, profile num, job_id
if __name__ == '__main__':
    global_setup_file = './evaluation/evaluation_config.yml'
    with open(global_setup_file, "r") as gyamlfile:
        gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
        total_job = gconfig['total_job']
        avg_interval = gconfig['avg_interval']
        time_intervals = np.random.exponential(
            scale=avg_interval, size=total_job - 1)

        job_profile_num = gconfig['job_profile_num']

        file_path = f"./evaluation/job/job_trace_{total_job}.txt"

        if not os.path.exists(file_path):
            with open(file_path, "w") as file:
                job_id = 0
                file.write(f'0 0\n')
                job_id += 1
                for i in time_intervals:
                    file.write(f'{int(i)} {job_id % job_profile_num}\n')
                    job_id += 1