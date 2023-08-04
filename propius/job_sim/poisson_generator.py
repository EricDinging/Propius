import yaml
import random
import numpy as np

random.seed(42)

# generate txt with format: time in minute, profile num, job_id
if __name__ == '__main__':
    global_setup_file = './global_config.yml'
    with open(global_setup_file, "r") as gyamlfile:
        gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
        total_running_second = gconfig['total_running_second']
        total_job = gconfig['total_job']
        
        avg_interval = total_running_second / total_job
        time_intervals = np.random.exponential(scale=avg_interval, size=total_job-1)

        job_profile_num = gconfig['job_profile_num']

        with open(f"./propius/job_sim/job_trace_{total_job}.txt", "w") as file:
            time = 0
            job_id = 0
            file.write(f'0 0 {job_id}\n')
            job_id += 1

            for i in time_intervals:
                time += i
                if time >= total_running_second:
                    break
                file.write(f'{int(i)} {job_id % job_profile_num} {job_id}\n')
                job_id += 1
            
