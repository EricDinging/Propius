import os
import csv
import yaml
import re
import matplotlib.pyplot as plt


global_config_file = './propius/global_config.yml'
with open(global_config_file, 'r') as gconfig:
    gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)

sched_alg = gconfig['sched_alg']

ps_folder = f'./evaluation_result/run_1_fifo/ps_result'
executor_folder = f'./evaluation_result/run_1_fifo/'

plot_folder = f'./evaluation_result/run_1_fifo/plot'

# test
pattern = r"_(\d+)\.csv"

for exe_res_name in os.listdir(executor_folder):
    match = re.search(pattern, exe_res_name)
    if match:
        exe_res_file_path = os.path.join(executor_folder, exe_res_name)
        job_id = match.group(1)

        ps_result_file_name = f"{job_id}.csv"
        ps_result_file_path = os.path.join(ps_folder, ps_result_file_name)

        time_stamp_list = []
        acc_list = []
        acc_5_list = []
        round_list = []

        with open(exe_res_file_path, "r") as exe_file:
            reader = csv.reader(exe_file)
            header = next(reader)

            acc_idx = header.index("acc")
            acc_5_idx = header.index("acc_5")
            round_idx = header.index("round")
            for row in reader:
                round_list.append(int(row[round_idx]))
                acc_list.append(float(row[acc_idx]))
                acc_5_list.append(float(row[acc_5_idx]))

        with open(ps_result_file_path, "r") as ps_file:
            reader = csv.reader(ps_file)
            header = next(reader)

            idx = header.index("round_finish_time")
            round_idx = header.index("round")
            for row in reader:
                round_num = int(row[round_idx])
                if round_num in round_list:
                    time_stamp_list.append(float(row[idx]))

        

        plt.figure(figsize=(10, 6))

        plt.plot(time_stamp_list, acc_list, label='acc')
        plt.plot(time_stamp_list, acc_5_list, label='acc_5')

        plt.xlabel('Time (seconds)')
        plt.ylabel('Accuracy')
        plt.title(f'Job {job_id} Time to Accuracy')
        plt.grid(True)

        plt.legend()

        output_plot_name = f'tta{job_id}.png'
        output_plot_path = os.path.join(plot_folder, output_plot_name)
        plt.savefig(output_plot_path)
        





