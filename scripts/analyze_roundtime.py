import os
import csv

folder_path = input("Enter the folder path containing CSV files: ")
def read_last_line(csv_file):
    with open(csv_file, 'r', newline='') as file:
        csv_reader = csv.reader(csv_file)
        last_row = None
        round_time = 0
        for row in csv_reader:
            if row[1] != -1:
                round_time = row[1]
            last_row = row
        if last_row is not None:
            return (round_time, last_row[2], last_row[3])
        
for filename in os.listdir(folder_path):
    upper_round = lower_round = upper_sched = lower_sched = upper_resp = lower_resp = 0
    total_round = total_sched = total_resp = 0
    num = 0
    if filename.endwith(folder_path):
        csv_file_path = os.path.join(folder_path, filename)
        round_time, sched, response = read_last_line(csv_file_path)

        num +=1 
        total_round += round_time
        total_sched += sched
        total_resp += response

        upper_round = round_time if round_time > upper_round else upper_round
        lower_round = round_time if round_time < lower_round else lower_round
        upper_sched = sched if sched > upper_sched else upper_sched
        lower_sched = sched if sched < lower_sched else lower_sched
        upper_resp = response if response > upper_resp else upper_resp
        lower_resp = response if response < lower_resp else lower_resp
avg_round = total_round / num
avg_sched = total_sched / num
avg_response = total_resp / num
print(f"Avg finish time: {avg_round}, avg sched delay: {avg_sched}, avg response time: {avg_response}")
print(f"Upper finish time: {upper_round}, Lower finish time: {lower_round}")
print(f"Upper sched time: {upper_sched}, Lower sched time: {lower_sched}")
print(f"Upper response time: {upper_resp}, Lower response time: {lower_resp}")

