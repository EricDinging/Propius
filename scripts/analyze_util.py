import re

def extract_utilize_time(log_file_path_list):
    utilize_times = []
    pattern = r"utilize_time\/total_time: (\d+\.\d+)"
    
    for log_file_path in log_file_path_list:
        with open(log_file_path, 'r') as file:
            for line in file:
                match = re.search(pattern, line)
                if match:
                    utilize_time = float(match.group(1))
                    print(utilize_time)
                    utilize_times.append(utilize_time)

    avg = sum(utilize_times) / len(utilize_times)
    return avg
        

log_file_path_list = [
    "./experiment/job_5_client_1500_random/client/print_0.log",
    "./experiment/job_5_client_1500_random/client/print_1.log",
    "./experiment/job_5_client_1500_random/client/print_2.log",
]

total_time = 19093.5396

avg_utilize_time = extract_utilize_time(log_file_path_list)
print("AVG Utilize Time:", avg_utilize_time)
print("Utilization Rate: ", avg_utilize_time / total_time)