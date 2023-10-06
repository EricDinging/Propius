import os
import csv
import yaml
import re
import matplotlib.pyplot as plt
import numpy as np

version = "6000-mixed"
time_cutoff = 60000
round_cutoff = 350

sched_alg_list = [
                #   'fifo',
                #   'random',
                  'srsf',
                  'amg'
                  ]

plot_option = 'acc' 
# plot_option = 'test_loss'

plot_folder = f'./evaluation_result/plot-{version}'
line_styles = ['-.', ':', '-']
color_list = ['grey', 'gold', 'darkorange', 'blueviolet', 'teal', 'skyblue' ,'darkblue', 'blueviolet']
job_num = 10

job_group_list = [(0, 2, 1), (5, 4, 3), (6, 8, 7, 9)]
job_group_end_time = {job_group: [] for job_group in job_group_list}

if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)

plt.figure(figsize=(5.4, 4))
round_info_dict = {}
# for sched_alg in sched_alg_list:
#     for job_id in range(job_num):
#         round_info_dict[f"{job_id}-{sched_alg}"] = 0

for i, sched_alg in enumerate(sched_alg_list):
    if sched_alg == 'amg':
        sched_alg = 'irs2'
    pattern = re.compile(f"test_(\d+)\_{sched_alg}.csv")
    round_list_dict = {}
    round_time_list_dict = {}
    acc_list_dict = {}
    avg_tloss_dict = {}
    end_time_list = []

    execute_folder = f'data/{sched_alg}-{version}/executor'
    job_folder = f'data/{sched_alg}-{version}/job'

    for exe_res_name in os.listdir(execute_folder):
        match = re.search(pattern, exe_res_name)
        if match:
            exe_res_file_path = os.path.join(execute_folder, exe_res_name)
            job_id = match.group(1)

            ps_result_file_name = f"job_{job_id}_{sched_alg}.csv"
            ps_result_file_path = os.path.join(job_folder, ps_result_file_name)

            time_stamp_list = [0]
            acc_list = []
            acc_5_list = []
            round_list = []
            avg_tloss_list = []

            with open(exe_res_file_path, "r") as exe_file:
                reader = csv.reader(exe_file)
                header = next(reader)
                acc_idx = header.index("acc")
                acc_5_idx = header.index("acc_5")
                round_idx = header.index("round")
                avg_loss_idx = header.index("test_loss")
                for row in reader:
                    round = int(row[round_idx])
                    round_list.append(round)
                    acc_list.append(float(row[acc_idx]))
                    avg_tloss_list.append(float(row[avg_loss_idx]))
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
                    if int(row[0]) == -1:
                        break
                    if round_time > time_cutoff:
                        break
                    if round_num in round_list:
                        time_stamp_list.append(round_time)
                    if round_num == round_cutoff:
                        break
            
            acc_list = acc_list[0:len(time_stamp_list)]
            avg_tloss_list = avg_tloss_list[0:len(time_stamp_list)]
            # round_list = round_list[0:len(time_stamp_list)]
            
            job_id = int(job_id) % 100
            
            # round_list_dict[job_id] = round_list
            round_info_dict[f"{job_id}-{sched_alg}"] = time_stamp_list[-1]

            if time_stamp_list[-1] > time_cutoff:
                continue
            end_time_list.append(time_stamp_list[-1])

            for job_group, group_end_time_list in job_group_end_time.items():
                if job_id in job_group:
                    group_end_time_list.append(time_stamp_list[-1])
                    break

            round_time_list_dict[job_id] = time_stamp_list
            acc_list_dict[job_id] = acc_list
            avg_tloss_dict[job_id] = avg_tloss_list

    avg_end_time = sum(end_time_list) / len(end_time_list)
    end_time = max(end_time_list)
    round_info_dict[f"avg-{sched_alg}"] = (avg_end_time, end_time)
    
    for group_idx, job_group in enumerate(job_group_list):
        end_time = sum(job_group_end_time[job_group]) / len(job_group_end_time[job_group])
        mean_x_axis = [i for i in range(int(end_time))]

        if plot_option == 'acc':
            ys_interp = [np.interp(mean_x_axis, round_time_list_dict[j], acc_list_dict[j]) for j in job_group]
        elif plot_option == 'test_loss':
            ys_interp = [np.interp(mean_x_axis, round_time_list_dict[j], avg_tloss_dict[j]) for j in job_group]
        
        mean_y_axis = np.mean(ys_interp, axis=0)

        if sched_alg == 'irs2':
            alg_label = 'AMG'
        elif sched_alg == 'fifo':
            alg_label = 'FIFO'
        elif sched_alg == 'random':
            alg_label = 'Random'
        elif sched_alg == 'srsf':
            alg_label = 'SRSF'

        plt.plot(mean_x_axis, mean_y_axis, label=f"{alg_label}, {job_group}", color=color_list[i], linestyle=line_styles[group_idx])



    # plot mean
    # mean_x_axis = [i for i in range(int(end_time))]
    # if plot_option == 'acc':
    #     ys_interp = [np.interp(mean_x_axis, round_time_list_dict[j], acc_list_dict[j]) for j in range(job_num)]
    # elif plot_option == 'test_loss':
    #     ys_interp = [np.interp(mean_x_axis, round_time_list_dict[j], avg_tloss_dict[j]) for j in range(job_num)]

    # mean_y_axis = np.mean(ys_interp, axis=0)
    # if sched_alg == 'irs2':
    #     alg_label = 'AMG'
    # elif sched_alg == 'fifo':
    #     alg_label = 'FIFO'
    # elif sched_alg == 'random':
    #     alg_label = 'Random'
    # elif sched_alg == 'srsf':
    #     alg_label = 'SRSF'
    # plt.plot(mean_x_axis, mean_y_axis, label=f"Policy: {alg_label}", color=color_list[i])

    # Indivial job
    # for job_id in range(job_num):
    #     if job_id == 0:
    #         label_text = "Mobilenet, FedAvg"
    #     elif job_id == 1:
    #         label_text = "Mobilenet, FedYogi"
    #     elif job_id == 2:
    #         label_text = "Resnet18, FedAvg"
    #     elif job_id == 3:
    #         label_text = "Resnet18, FedYogi"
    #     plt.plot(round_time_list_dict[job_id], acc_list_dict[job_id], label=label_text, color=color_list[job_id], linestyle=line_styles[i])

            # if job_id < job_num:
            #     plt.plot(round_time_list_dict[job_id], acc_list_dict[job_id], label=f"Job: {job_id}, sched. alg: {sched_alg}", color=color_list[job_id], linestyle=line_styles[i])


plt.xlabel('Time (seconds)')

if plot_option == 'acc':
    plt.ylabel('Accuracy')
elif plot_option == 'test_loss':
    plt.ylabel("Avg. Testing Loss")
# plt.title(f'Average Job Time to Accuracy Plot under Various Scheduling Policies, FEMNIST, {version}')
# plt.ylim([0.6, 0.8])
# plt.xlim([10000, 20000])
plt.grid(True)
plt.legend()

# output_plot_name = f'tta-acc-no-irs.png'
output_plot_name = f"{plot_option}-{version}.png"
output_plot_path = os.path.join(plot_folder, output_plot_name)
plt.savefig(output_plot_path)

output_file_name = f'round.txt'
output_file_path = os.path.join(plot_folder, output_file_name)
with open(output_file_path, "w") as file:
    for key, value in round_info_dict.items():
        file.write(f"{key} - {value}\n")
        





