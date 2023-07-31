import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time
import json
from propius.util.db import *

class Job_db_stub(Job_db):
    def __init__(self, gconfig):
        super().__init__(gconfig)

    def client_assign(self, specification:tuple)->tuple[list, list, int]:
        q = Query('*').sort_by('score', asc=False)
        try:
            result = self.r.ft('job').search(q)
        except:
            result = None
        if result:
            size = result.total
            for doc in result.docs:
                    job = json.loads(doc.json)
                    job_public_constraint = tuple([job['job']['public_constraint'][name]
                                                    for name in self.public_constraint_name])
                    if job['job']['amount'] < job['job']['demand'] and geq(specification, job_public_constraint):
                        job_private_constraint = tuple([job['job']['private_constraint'][name]
                                                        for name in self.private_constraint_name])
                        return [int(doc.id.split(':')[1])], [job_private_constraint], size
            return [], [], size
        return [], [], 0
    
    def incr_amount(self, job_id:int)->tuple[str, int]:
        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"job:{job_id}"
                    pipe.watch(id)
                    amount = int(self.r.json().get(id, "$.job.amount")[0])
                    if amount is None:
                        pipe.unwatch()
                        return None
                    demand = int(self.r.json().get(id, "$.job.demand")[0])
                    ip = str(self.r.json().get(id, "$.job.ip")[0])
                    port = int(self.r.json().get(id, "$.job.port")[0])

                    if amount >= demand:
                        pipe.unwatch()
                        return None
                    else:
                        pipe.multi()
                        pipe.execute_command('JSON.NUMINCRBY', id, "$.job.amount", 1)
                        if amount == demand - 1:
                            start_sched = float(self.r.json().get(id, "$.job.start_sched")[0])
                            sched_time = time.time() - start_sched
                            pipe.execute_command('JSON.NUMINCRBY',  id, "$.job.total_sched", sched_time)
                        pipe.execute()
                        return (ip, port)
                except redis.WatchError:
                    pass

class Client_db_stub(Client_db):
    def __init__(self, gconfig):
        super().__init__(gconfig)
    
    def insert(self, id:int, specifications:tuple):
        if len(specifications) != len(self.public_constraint_name):
            raise ValueError("Specification length does not match required")
        client_dict = {"timestamp": int(time.time())}
        spec_dict = {self.public_constraint_name[i] : specifications[i]
                     for i in range(len(specifications))}
        client_dict.update(spec_dict)
        client = {
            "client":client_dict
        }
        self.r.json().set(f"client:{id}", Path.root_path(), client)
        self.r.expire(f"client:{id}", self.client_ttl)