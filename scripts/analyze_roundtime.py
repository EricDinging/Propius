"""A python script that performs analysis on JCT, scheduling latency and
response time across all simulated jobs
"""

import os
import csv

folder_path = input("Enter the folder path containing CSV files: ")

if not os.path.exists(folder_path):
    raise FileNotFoundError("The specified folder does not exist.")
def read_last_line(csv_file):
    with open(csv_file, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        round_time = 0
        sched_time = 0
        resp_time = 0
        last_row = None
        for row in csv_reader:
            print(row)
            if row[0] == "-1":
                round_time = float(last_row[1])
                sched_time = float(row[2])
                resp_time = float(row[3])
            last_row = row

def read_first(round, csv_file):
    with open(csv_file, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        time_round = 0
        sched_time = 0
        resp_time = 0
        num = 0
        for row in csv_reader:
            if row[0] == "round":
                continue
            sched_time += float(row[2])
            resp_time += float(row[3])
            num += 1
            if num == round:
                time_round = float(row[1])
                break

        sched_time /= num if num > 0 else 1
        resp_time /= num if num > 0 else 1
    
        return (time_round, sched_time, resp_time)

analyze_certain_rounds = input("Analyze certain rounds y/n: ") == 'y'

if analyze_certain_rounds:
    round = int(input("round: "))
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            csv_file_path = os.path.join(folder_path, filename)
            round_time, sched, response = read_first(round, csv_file_path)
            print(f"{filename}, round: {round} time: {round_time}, avg sched: {sched}, avg_response: {response}")
else:
    upper_round = upper_sched = upper_resp =  0
    total_round = total_sched = total_resp = 0
    lower_round = lower_sched = lower_resp = 1000000000
    num = 0  
    for filename in os.listdir(folder_path):
        
        if filename.endswith(".csv"):
            csv_file_path = os.path.join(folder_path, filename)
            # print(csv_file_path)
            round_time, sched, response = read_last_line(csv_file_path)

            num += 1 
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

