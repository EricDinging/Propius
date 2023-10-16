import numpy as np
import csv
import os
import re
# Define your threshold for relative change
threshold = 0.01  # 1% change
# folder = 'evaluation_result/irs3-6000-var/executor/'
sched_alg = 'irs3'
folder = f'evaluation_result/{sched_alg}-6000-var/executor/'

predetermined = True
round_cutoff = [70, 105, 110, 70, 125, 80, 105, 110, 45, 140]

pattern = re.compile(f"test_(\d+)\_{sched_alg}.csv")

def read_file(csv_file):
    csv_file_path = os.path.join(folder, csv_file)
    with open(csv_file_path, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        test_acc_list = []
        acc_idx = 3
        round_num = 0
        round_idx = 0

        match = re.search(pattern, csv_file)
        job_id = int(match.group(1)) % 10

        round_break = round_cutoff[job_id]

        consecutive_below_threshold = 0
        for row in csv_reader:
            if row[0] == 'round':
                continue
            test_acc_list.append(float(row[acc_idx]))
            round_num = int(row[round_idx])
            
            if not predetermined:
                if round_num >= 2:
                    relative_change = (test_acc_list[-1] - test_acc_list[-2]) / test_acc_list[-2]
                    if relative_change < threshold:
                        consecutive_below_threshold += 1
                    else:
                        consecutive_below_threshold = 0
                
                if consecutive_below_threshold >= 3:
                    break
            else:
                if round_num >= round_break:
                    break

        return round_num, test_acc_list[-1]

job_info_map = {}
total_acc = 0
for filename in os.listdir(folder):
    if filename.endswith(".csv") and filename[:4] == "test":
        round_num, acc = read_file(filename)
        print(f"{filename}: {round_num, acc}")

        job_info_map[filename] = acc
        total_acc += acc

job_info_map = dict(sorted(job_info_map.items()))
print("File: acc")
for key, val in job_info_map.items():
    print(f"{key}: {val}")

print(f"Avg acc: {total_acc / len(job_info_map):.3f}")


