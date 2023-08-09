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


class CM_job_db_portal(Job_db):
    def __init__(self, gconfig):
        """Initialize job db portal

        Args:
            gconfig: config dictionary
                job_db_ip
                job_db_port
                sched_alg
                job_public_constraint: name of public constraint
                job_private_constraint: name of private constraint
            is_jm: a bool indicating whether the user of the database is job manager
        """

        super().__init__(gconfig, False)

    def client_assign(self, specification: tuple) -> tuple[list, list, int]:
        """Assign tasks to client with input specification. 
        The client public specification would satisfy returned task public constraints, 
        but client private specification might not satisfy the returned task private constraints. 
        The returned tasks' current allocation amount would be smaller than their respective demand

        Args:
            specification: a tuple listing public spec values
        
        Returns:
            task_offer_list: list of job id, with size no greater than max_task_len
            task_private_constraint_list: list of tuple of private constraint 
                                            for client local task selection
            size: total number of jobs for analytics
        """

        q = Query('*').sort_by('score', asc=False)
        try:
            result = self.r.ft('job').search(q)
        except BaseException:
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
            # return open_list + upd_proactive_list, open_private_constraint +
            # upd_proactive_private_constraint, size
            return open_list, open_private_constraint, size

        return [], [], 0

    def incr_amount(self, job_id: int) -> tuple[str, int]:
        """Increase the job allocation amount if current allocation amount is less than demand, 
        and returns job parameter server address. If current allocation amount is no less than demand,
        allocation amount will not be further increased, and address will not be returned (assign abort)

        Args:
            job_id

        Returns:
            parameter_server_ip:
            parameter_server_port 
        """

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

                    round = int(self.r.json().get(id, "$.job.round")[0])
                    total_round = int(
                        self.r.json().get(
                            id, "$.job.total_round")[0])
                    
                    if amount >= demand:
                        pipe.unwatch()
                        return None

                    pipe.multi()
                    if amount < demand:
                        pipe.execute_command(
                            'JSON.NUMINCRBY', id, "$.job.amount", 1)
                    if amount == demand - 1:
                        start_sched = float(
                            self.r.json().get(
                                id, "$.job.start_sched")[0])
                        sched_time = time.time() - start_sched
                        pipe.execute_command(
                            'JSON.NUMINCRBY', id, "$.job.total_sched", sched_time)
                    pipe.execute()
                    return (ip, port)
                except redis.WatchError:
                    pass


class CM_client_db_portal(Client_db):
    def __init__(self, gconfig, cm_id: int):
        """Initialize client db portal

        Args:
            gconfig: config dictionary
                client_manager: list of client manager address
                    ip:
                    client_db_port
                client_expire_time: expiration time of clients in the db
                job_public_constraint: name of public constraint

            cm_id: id of the client manager is the user is client manager
            is_cm: bool indicating whether the user is client manager
        """

        super().__init__(gconfig, cm_id, True)

    def insert(self, id: int, specifications: tuple):
        """Insert client metadata to database, set expiration time and start time

        Args:
            id
            specification: a tuple of public spec values
        """

        if len(specifications) != len(self.public_constraint_name):
            raise ValueError("Specification length does not match required")
        client_dict = {"timestamp": int(time.time())}
        spec_dict = {self.public_constraint_name[i]: specifications[i]
                     for i in range(len(specifications))}
        client_dict.update(spec_dict)
        client = {
            "client": client_dict
        }
        self.r.json().set(f"client:{id}", Path.root_path(), client)
        self.r.expire(f"client:{id}", self.client_exp_time)

    def get(self, id: int) -> tuple:
        """Get client public spec values

        Args:
            id

        Returns:
            specs: a tuple of public spec values
        """

        id = f"client:{id}"
        specs = [0] * len(self.public_constraint_name)
        try:
            for idx, name in enumerate(self.public_constraint_name):
                spec = int(self.r.json().get(id, f"$.client.{name}")[0])
                specs[idx] = spec
        except BaseException:
            pass
        return tuple(specs)
