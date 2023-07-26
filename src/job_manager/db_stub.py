import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time
import json
from propius.src.util.db import *

class Job_db_stub(Job_db):
    def __init__(self, gconfig):
        super().__init__(gconfig)

    def register(self, job_id:int, constraints:tuple[int, int, int], job_ip:str
                 , job_port:int, total_demand:int, total_round:int)->bool:
        job = {
            "job":{
                "timestamp": time.time(),
                "total_sched": 0,
                "start_sched": 0,
                "constraints": {
                    "cpu": constraints[0],
                    "memory": constraints[1],
                    "os": constraints[2]
                },
                "ip": job_ip,
                "port": job_port,
                "total_demand": total_demand,
                "total_round": total_round,
                "round": 0,
                "demand": 0,
                "amount": 0,
                "score": 0,
            }
        }

        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"job:{job_id}"
                    pipe.watch(id)
                    if pipe.get(id):
                        pipe.unwatch()
                        return False
                    pipe.set(id, Path.root_path(), job)
                    pipe.unwatch()
                    return True
                except redis.WatchError:
                    pass
    
    def request(self, job_id:int, demand:int)->bool:
        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"job:{job_id}"
                    pipe.watch(id)
                    if not pipe.get(id):
                        pipe.unwatch()
                        return False
                    pipe.multi()
                    pipe.execute_command('JSON.NUMINCRBY', id, "$.job.round", 1)
                    pipe.execute_command('JSON.SET', id, "$.job.demand", demand)
                    pipe.execute_command('JSON.SET', id, "$.job.amount", 0)
                    pipe.execute_command('JSON.SET', id, "$.job.start_sched", time.time())
                    pipe.execute()
                    return True
                except redis.WatchError:
                    pass
        
    def finish(self, job_id:int)->tuple[tuple[int, int, int], int, int, float, float]:
        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"job:{job_id}"
                    pipe.watch(id)
                    start_time = float(self.r.json().get(id, "$.job.timestamp")[0])
                    total_sched = float(self.r.json().get(id, "$.job.total_sched")[0])
                    round = float(self.r.json().get(id, "$.job.round")[0])
                    cpu = int(self.r.json().get(id, "$.job.constraints.cpu")[0])
                    memory = int(self.r.json().get(id, "$.job.constraints.memory")[0])
                    os = int(self.r.json().get(id, "$.job.constraints.os")[0])
                    demand = int(self.r.json().get(id, "$.job.demand")[0])
                    total_round = int(self.r.json().get(id, "$.job.total_round")[0])
                    runtime = time.time() - start_time
                    sched_latency = total_sched / round if round > 0 else -1
                    pipe.delete(id)
                    pipe.unwatch()
                    return ((cpu, memory, os), demand, total_round, runtime, sched_latency)
                except redis.WatchError:
                    pass

class Client_db_stub(Client_db):
    def __init__(self, gconfig):
        super().__init__(gconfig)

    # async def cleanup(self):
    #     self._cleanup()