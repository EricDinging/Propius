import asyncio
from evaluation.commons import *
from collections import deque

class Task_pool:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.job_meta_dict = {}
        self.job_task_dict = {}
        self.cur_job_id = -1
        self.result_dict = {}

    async def init_job(self, job_id: int, job_meta: dict):
        async with self.lock:
            self.job_meta_dict[job_id] = job_meta
            self.job_task_dict = deque()
    
    async def insert_job_task(self, job_id: int, client_id: int, round: int, event: str, task_meta: dict):
        """event: {MODEL_TRAIN, AGGREGATE}
        """
        task_meta["client_id"] = client_id
        task_meta["round"] = round
        task_meta["event"] = event
        
        async with self.lock:
            assert job_id in self.job_meta_dict
            assert job_id in self.job_task_dict

            self.job_meta_dict[job_id].append(task_meta)

    async def get_next_task(self)->dict:
        """Get next task, prioritize previous job id if there is still task left for the job
        """
        async with self.lock:
            if self.cur_job_id in self.job_meta_dict and len(self.job_task_dict[self.cur_job_id]) > 0:
                execute_meta = job_meta.update(self.job_meta_dict[self.cur_job_id].popleft())
                return execute_meta
            
            for job_id, job_meta in self.job_meta_dict.items():
                if len(self.job_task_dict[job_id]) > 0:
                    execute_meta = job_meta.update(self.job_task_dict[job_id].popleft())
                    self.cur_job_id = job_id
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
            if job_id not in self.result_dict:
                self.result_dict[job_id] = {}
            
            if round not in self.result_dict[job_id]:
                self.result_dict[job_id][round] = {}

            self.result_dict[job_id][round].update(result)
    
    def gen_report(self):
        for job_id, round_result_dict in self.result_dict.items():
            print(f"Job {job_id}: ")
            for round, result in round_result_dict.items():
                print(f"    Round {round}: {result}")