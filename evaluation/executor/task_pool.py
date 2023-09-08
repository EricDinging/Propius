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
        self.job_meta_dict = {}
        self.job_task_dict = {}
        self.cur_job_id = -1
        self.config = config
        self.select_time = 0

    async def init_job(self, job_id: int, job_meta: dict):
        async with self.lock:
            job_meta["job_id"] = job_id
            self.job_meta_dict[job_id] = job_meta

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
            assert job_id in self.job_meta_dict
            assert job_id in self.job_task_dict

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
            if self.cur_job_id in self.job_meta_dict \
                and len(self.job_task_dict[self.cur_job_id]) > 0 \
                    and self.select_time < 50:
                execute_meta = copy.deepcopy(self.job_meta_dict[self.cur_job_id])
                execute_meta.update(self.job_task_dict[self.cur_job_id].popleft())
                self.select_time += 1
                return execute_meta
            
            for job_id, job_meta in self.job_meta_dict.items():
                if len(self.job_task_dict[job_id]) > 0:
                    execute_meta = copy.deepcopy(job_meta)
                    execute_meta.update(self.job_task_dict[job_id].popleft())
                    self.cur_job_id = job_id
                    self.select_time = 1
                    return execute_meta
            return None
        
    async def remove_job(self, job_id: int):
        async with self.lock:

            try:
                del self.job_meta_dict[job_id]
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

