import asyncio
from evaluation.commons import *
from collections import deque
import random
import copy
import csv
import os

class Task_pool:
    def __init__(self, config):
        self.lock = asyncio.Lock()
        self.job_meta_list = deque()
        self.job_task_dict = {}
        self.config = config
        self.select_time = 0

    async def init_job(self, job_id: int, job_meta: dict):
        async with self.lock:
            job_meta["job_id"] = job_id
            self.job_meta_list.append(job_meta)

            self.job_task_dict[job_id] = deque()
            test_task_meta = {
                "client_id": random.randint(0, 10000),
                "round": 0,
                "event": MODEL_TEST,
                "test_ratio": self.config["test_ratio"],
                "test_bsz": self.config["test_bsz"]
            }
            self.job_task_dict[job_id].append(test_task_meta)

            test_csv_file_name = f"./evaluation/monitor/executor/test_{job_id}_{self.config['sched_alg']}.csv"
            os.makedirs(os.path.dirname(test_csv_file_name), exist_ok=True)
            fieldnames = ["round", "test_loss", "acc", "acc_5", "test_len"]
            with open(test_csv_file_name, "w", newline="") as test_csv:
                writer = csv.DictWriter(test_csv, fieldnames=fieldnames)
                writer.writeheader()
            
    
    async def insert_job_task(self, job_id: int, client_id: int, round: int, event: str, task_meta: dict):
        """event: {CLIENT_TRAIN, AGGREGATE, FINISH}
        """
        task_meta["client_id"] = client_id
        task_meta["round"] = round
        task_meta["event"] = event
        
        async with self.lock:
            if job_id not in self.job_task_dict:
                return

            test_task_meta = {
                    "client_id": -1,
                    "round": task_meta["round"],
                    "event": MODEL_TEST,
                    "test_ratio": self.config["test_ratio"],
                    "test_bsz": self.config["test_bsz"]
                }
            
            if event == JOB_FINISH:
                self.job_task_dict[job_id].append(test_task_meta)

            self.job_task_dict[job_id].append(task_meta)

            if event == AGGREGATE and round % self.config["eval_interval"] == 0:
                test_task_meta = {
                    "client_id": -1,
                    "round": task_meta["round"],
                    "event": MODEL_TEST,
                    "test_ratio": self.config["test_ratio"],
                    "test_bsz": self.config["test_bsz"]
                }
                self.job_task_dict[job_id].append(test_task_meta)


    async def get_next_task(self)->dict:
        """Get next task, prioritize previous job id if there is still task left for the job
        """
        async with self.lock:
            job_num = len(self.job_meta_list)
            for _ in range(job_num):
                job_meta = copy.deepcopy(self.job_meta_list[0])
                job_id = job_meta["job_id"]
                if len(self.job_task_dict[job_id]) > 0 and self.select_time < 50:
                    job_meta.update(self.job_task_dict[job_id].popleft())
                    self.select_time += 1
                    return job_meta
                self.select_time = 0
                self.job_meta_list.append(self.job_meta_list.popleft())
            return None
        
    async def remove_job(self, job_id: int):
        async with self.lock:

            try:
                temp_deque = deque()
                while self.job_meta_list:
                    job_meta = self.job_meta_list.popleft()
                    if job_meta["job_id"] == job_id:
                        break
                    temp_deque.append(job_meta)
                while temp_deque:
                    self.job_meta_list.appendleft(temp_deque.pop())

                del self.job_task_dict[job_id]
            except:
                pass

    
    async def report_result(self, job_id: int, round: int, result: dict):
        async with self.lock:
            test_csv_file_name = f"./evaluation/monitor/executor/test_{job_id}_{self.config['sched_alg']}.csv"
            fieldnames = ["round", "test_loss", "acc", "acc_5", "test_len"]
            os.makedirs(os.path.dirname(test_csv_file_name), exist_ok=True)
            with open(test_csv_file_name, mode="a", newline="") as test_csv:
                writer = csv.DictWriter(test_csv, fieldnames=fieldnames)
                result["round"] = round
                writer.writerow(result)

