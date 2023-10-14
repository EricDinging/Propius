import numpy as np
import csv
import os
# Define your threshold for relative change
threshold = 0.01  # 1% change
folder = 'evaluation_result/fifo-6000-new/executor/'

def read_file(csv_file):
    with open(csv_file, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        test_acc_list = []
        acc_idx = 3
        round_num = 0
        round_idx = 0

        consecutive_below_threshold = 0
        for row in csv_reader:
            if row[0] == 'round':
                continue
            test_acc_list.append(float(row[acc_idx]))
            round_num = int(row[round_idx])
            
            if round_num >= 2:
                relative_change = (test_acc_list[-1] - test_acc_list[-2]) / test_acc_list[-2]
                if relative_change < threshold:
                    consecutive_below_threshold += 1
                else:
                    consecutive_below_threshold = 0
            
            if consecutive_below_threshold >= 3:
                break
        
        return round_num

for filename in os.listdir(folder):
    if filename.endswith(".csv") and filename[:4] == "test":
        csv_file_path = os.path.join(folder, filename)
        print(f"{filename}: {read_file(csv_file_path)}")
