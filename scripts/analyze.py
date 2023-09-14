import os
import csv
import yaml
import re
import matplotlib.pyplot as plt

time_cutoff = 500000
round_cutoff = 200
sched_alg_list = ['fifo', 
                  'random', 
                  'irs']
job_folder = ['./evaluation_result/fifo-3000-2/job',
              './evaluation_result/random-3000-2/job',
              './evaluation_result/irs-3000-2/job']
execute_folder = ['./evaluation_result/fifo-3000-2/executor',
                  './evaluation_result/random-3000-2/executor',
                  './evaluation_result/irs-3000-2/executor']

# client_num = [3000, 5000]

plot_folder = f'./evaluation_result/plot-3000-2'
line_styles = [
            '-.', 
               ':', 
               '-']
# color_list = ['grey',  'blueviolet', 'gold', 'darkorange','teal', 'skyblue' ,'darkblue', 'blueviolet']
color_list = ['blueviolet', 'darkorange', 'teal', 'skyblue', 'darkblue']
job_num = 5

# test

plt.figure(figsize=(10.8, 8))
round_info_dict = {}
# for sched_alg in sched_alg_list:
#     for job_id in range(job_num):
#         round_info_dict[f"{job_id}-{sched_alg}"] = 0

for i, sched_alg in enumerate(sched_alg_list):
    pattern = re.compile(f"test_(\d+)\_{sched_alg}.csv")
    round_list_dict = {}
    round_time_list_dict = {}
    acc_list_dict = {}
    for exe_res_name in os.listdir(execute_folder[i]):
        match = re.search(pattern, exe_res_name)
        if match:
            exe_res_file_path = os.path.join(execute_folder[i], exe_res_name)
            job_id = match.group(1)

            ps_result_file_name = f"job_{job_id}_{sched_alg}.csv"
            ps_result_file_path = os.path.join(job_folder[i], ps_result_file_name)

            time_stamp_list = [0]
            acc_list = []
            # acc_5_list = []
            round_list = []

            with open(exe_res_file_path, "r") as exe_file:
                reader = csv.reader(exe_file)
                header = next(reader)
                acc_idx = header.index("acc")
                acc_5_idx = header.index("acc_5")
                round_idx = header.index("round")
                for row in reader:
                    round = int(row[round_idx])
                    round_list.append(round)
                    acc_list.append(float(row[acc_idx]))
                    if round == round_cutoff:
                        break
                    
                    # acc_5_list.append(float(row[acc_5_idx]))
            round_num = 0
            with open(ps_result_file_path, "r") as ps_file:
                reader = csv.reader(ps_file)
                header = next(reader)

                idx = header.index("round_time")
                round_idx = header.index("round")
                for row in reader:
                    round_num = int(row[round_idx])
                    round_time = float(row[idx])
                    if round_time > time_cutoff:
                        break
                    if round_num in round_list:
                        time_stamp_list.append(round_time)
                    if round_num == round_cutoff:
                        break
            
            acc_list = acc_list[0:len(time_stamp_list)]
            # round_list = round_list[0:len(time_stamp_list)]
            job_id = int(job_id) % 100
            # round_list_dict[job_id] = round_list
            round_info_dict[f"{job_id}-{sched_alg}"] = round_num
            round_time_list_dict[job_id] = time_stamp_list
            acc_list_dict[job_id] = acc_list

    for job_id in range(job_num):       
        plt.plot(round_time_list_dict[job_id], acc_list_dict[job_id], label=f"Job: {job_id}, sched. alg: {sched_alg}", color=color_list[job_id], linestyle=line_styles[i])


plt.xlabel('Time (seconds)')
plt.ylabel('Accuracy')
# plt.title(f'Femnist Job Time to Accuracy under Various Scheduling Policies')
plt.ylim([0.6, 0.8])
plt.xlim([10000, 20000])
plt.grid(True)
plt.legend()

output_plot_name = f'tta.png'
output_plot_path = os.path.join(plot_folder, output_plot_name)
plt.savefig(output_plot_path)

output_file_name = f'round.txt'
output_file_path = os.path.join(plot_folder, output_file_name)
with open(output_file_path, "w") as file:
    for key, value in round_info_dict.items():
        file.write(f"{key} - {value}\n")
        





