import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time
import json
from propius.util.db import *
import random

class Job_db_stub(Job_db):
    def __init__(self, gconfig):
        super().__init__(gconfig, False)

    def client_assign(self, specification:tuple)->tuple[list, list, int]:
        q = Query('*').sort_by('score', asc=False)
        try:
            result = self.r.ft('job').search(q)
        except:
            result = None
        if result:
            size = result.total
            open_list = []
            open_private_constraint = []
            # proactive_list = []
            # proactive_private_constraint = []
            max_task_len = self.gconfig['max_task_offer_list_len']
            for doc in result.docs:
                    job = json.loads(doc.json)
                    job_public_constraint = tuple(
                        [job['job']['public_constraint'][name]
                            for name in self.public_constraint_name])
                    # if len(open_list) + len(proactive_list) >= max_task_len:
                    if len(open_list) >= max_task_len:
                        break
                    if geq(specification, job_public_constraint):
                        if job['job']['amount'] < job['job']['demand']:
                            open_list.append(int(doc.id.split(':')[1]))
                            job_private_constraint = tuple(
                            [job['job']['private_constraint'][name]
                                for name in self.private_constraint_name])
                            open_private_constraint.append(job_private_constraint)
                        
                        # elif self.gconfig['proactive']:
                        #     if job['job']['round'] < job['job']['total_round']:
                        #         proactive_list.append(int(doc.id.split(':')[1]))
                        #         job_private_constraint = tuple(
                        #         [job['job']['private_constraint'][name]
                        #             for name in self.private_constraint_name])
                        #         proactive_private_constraint.append(job_private_constraint)
            # upd_proactive_list = upd_proactive_private_constraint = []
            # if len(proactive_list) > 0:
            #     # Use random proactive scheduling
            #     combined_job = list(zip(proactive_list, proactive_private_constraint))
            #     random.shuffle(combined_job)
            #     upd_proactive_list, upd_proactive_private_constraint = zip(*combined_job)
            #     upd_proactive_list = list(upd_proactive_list)
            #     upd_proactive_private_constraint = list(upd_proactive_private_constraint)
            # return open_list + upd_proactive_list, open_private_constraint + upd_proactive_private_constraint, size
            return open_list, open_private_constraint, size
            
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
                    register_time = float(self.r.json().get(id, "$.job.timestamp")[0])
                    runtime = time.time() - register_time
                    round = int(self.r.json().get(id, "$.job.round")[0])
                    total_round = int(self.r.json().get(id, "$.job.total_round")[0])

                    if amount >= demand:
                        pipe.unwatch()
                        return None
                            
                    pipe.multi()
                    if amount < demand:
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
    def __init__(self, gconfig, cm_id:int):
        super().__init__(gconfig, cm_id, True)
    
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

    def get(self, id:int)->tuple:
        id = f"client:{id}"
        specs = [0] * len(self.public_constraint_name)
        try:
            for idx, name in enumerate(self.public_constraint_name):
                spec = int(self.r.json().get(id, f"$.client.{name}")[0])
                specs[idx] = spec
        except:
            pass
        return tuple(specs)
            