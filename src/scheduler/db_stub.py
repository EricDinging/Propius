import sys
sys.path.append('..')

import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time
import json
from src.util.db import *
import random

class Job_db_stub(Job_db):
    def __init__(self, gconfig):
        super().__init__(gconfig)
    
    def get_job_constraints(self, job_id:int)->tuple:
        id = f"job:{job_id}"
        constraint_list = []
        try:
            for name in self.public_constraint_name:
                constraint_list.append(int(self.r.json().get(id, f"$.job.public_constraint.{name}")[0]))
            return tuple(constraint_list)
        except:
            return None
    
    def get_job_list(self, public_constraint:tuple, constraints_job_list:list)->bool:
        job_total_demand_map = {}
        job_time_map = {}
        # if constraints exist, insert as a list to dict, return true
        qstr = ""
        for idx, name in enumerate(self.public_constraint_name):
            qstr += f"@{name}: [{public_constraint[idx]}, {public_constraint[idx]}] "
        
        q = Query(qstr)
        result = self.r.ft('job').search(q)
        if result.total == 0:
            return False

        for doc in result.docs:
            id = doc.id.split(':')[1]
            constraints_job_list.append(id)
            job_dict = json.loads(doc.json)["job"]
            job_total_demand_map[id] = job_dict["total_demand"]
            job_time_map[id] = job_dict['timestamp']
        constraints_job_list.sort(key=lambda x: (job_total_demand_map[x], job_time_map[x]))

        return True
    
    def irs_update_score(self, job:int, groupsize:int, idx:int, denominator:float, irs_epsilon:float=0, std_round_time:float=0):
        score = (groupsize - idx) / denominator
        if irs_epsilon > 0:
            sjct = self._get_job_SJCT(job, std_round_time)
            score = score * (self._get_job_time(job) / sjct)**irs_epsilon
        try:
            self.r.execute_command('JSON.SET', f"job:{job}", "$.job.score", score)
            print(f"job:{job} {score:.3f} ")
        except:
            pass


    def fifo_update_all_job_score(self):
        q = Query('@score: [0, 0]')
        result = self.r.ft('job').search(q)
        if result.total == 0:
            return
        for doc in result.docs:
            id = doc.id
            score = -json.loads(doc.json)["job"]["timestamp"]
            print(f"{id}: {score:.3f} ")
            self.r.execute_command('JSON.SET', id, "$.job.score", score)
    
    def random_update_all_job_score(self):
        q = Query('@score: [0, 0]')
        result = self.r.ft('job').search(q)
        if result.total == 0:
            return
        for doc in result.docs:
            id = doc.id
            job_size = self.get_job_size()
            score = random.uniform(0, 10)
            print(f"{id}: {score:.3f} ")
            self.r.execute_command('JSON.SET', id, "$.job.score", score)
    
    def srdf_update_all_job_score(self):
        q = Query('*')
        result = self.r.ft('job').search(q)
        if result.total == 0:
            return
        for doc in result.docs:
            id = doc.id
            job_dict = json.loads(doc.json)['job']
            remain_round = job_dict['total_round'] - job_dict['round']
            remain_demand = job_dict['demand'] * remain_round
            if remain_demand == 0:
                remain_demand = job_dict['total_demand']
            score = -remain_demand
            print(f"{id}: {score:.3f} ")
            self.r.execute_command('JSON.SET', id, "$.job.score", score)

    def srtf_update_all_job_score(self, std_round_time:float):
        q = Query('*')
        result = self.r.ft('job').search(q)
        if result.total == 0:
            return
        for doc in result.docs:
            id = doc.id
            job_dict = json.loads(doc.json)['job']
            remain_round = job_dict['total_round'] - job_dict['round']
            past_round = job_dict['round']
            if past_round == 0:
                avg_round_time = std_round_time
            else:
                avg_round_time = (time.time() - job_dict['timestamp']) / past_round
            remain_time = remain_round * avg_round_time
            score = -remain_time
            print(f"{id}: {score:.3f} ")
            self.r.execute_command('JSON.SET', id, "$.job.score", score)

    def _get_job_time(self, job_id:int)->float:
        id = f"job:{job_id}"
        try:
            timestamp = float(self.r.json().get(id, "$.job.timestamp")[0])
            return time.time() - timestamp
        except:
            return 0
        
    def _get_job_SJCT(self, job_id:int, std_round_time:float)->float:
        id = f"job:{job_id}"
        try:
            total_round = int(self.r.json().get(id, ".job.total_round")[0])
            return total_round * std_round_time
        except:
            return 1000 * std_round_time
        
class Client_db_stub(Client_db):
    def __init__(self, gconfig):
        super().__init__(gconfig)
        self.metric_scale = gconfig['metric_scale']

    def get_client_size(self)->int:
        info = self.r.ft('client').info()
        return int(info['num_docs'])

    def get_client_proportion(self, public_constraint:tuple)->float:
        client_size = self.get_client_size()
        if client_size == 0:
            return 0.01

        qstr = ""
        for idx, name in enumerate(self.public_constraint_name):
            qstr += f"@{name}: [{public_constraint[idx]}, {self.metric_scale}] "

        q = Query(qstr).no_content()
        size = int(self.r.ft('client').search(q).total)
        if size == 0:
            return 0.01

        return size / client_size
    
    def get_irs_denominator(self, client_size:int, q:str)->float:
        if client_size == 0:
            return 0.01
        q = Query(q).no_content()
        size = int(self.r.ft('client').search(q).total)

        if size == 0:
            return 0.01
        
        return size / client_size