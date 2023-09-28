import random
from propius.database.db import *
import json
import time
from redis.commands.search.query import NumericFilter, Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.field import TextField, NumericField, TagField
import redis.commands.search.reducers as reducers
from redis.commands.json.path import Path
import redis
import sys
from propius.util.commons import *

class SC_job_db_portal(Job_db):
    def __init__(self, gconfig, logger):
        """Initialize job db portal

        Args:
            gconfig: config dictionary
                job_db_ip
                job_db_port
                sched_alg
                job_public_constraint: name of public constraint
                job_private_constraint: name of private constraint
                job_expire_time
            logger
        """

        super().__init__(gconfig, False, logger)
        self.start_time = time.time()

    def get_job_constraints(self, job_id: int) -> tuple:
        """Get job constraint values of the job in a tuple

        Args:
            job_id: id of job
        """

        id = f"job:{job_id}"
        constraint_list = []
        try:
            for name in self.public_constraint_name:
                constraint_list.append(float(self.r.json().get(
                    id, f"$.job.public_constraint.{name}")[0]))
            return tuple(constraint_list)
        except Exception as e:
            self.logger.print(e, ERROR)
            return None

    def get_job_list(self, public_constraint: tuple,
                     constraints_job_list: list) -> bool:
        """Get all the jobs that has the input public constraint, 
        sorted by the total demand in ascending order

        Use register time to break tie 

        Args:
            public_constraint: constraint values listed in a tuple
            constraints_job_list: a list that the sorted job will be stored in
        """

        job_total_demand_map = {}
        job_time_map = {}
        # if constraints exist, insert as a list to dict, return true
        qstr = ""
        for idx, name in enumerate(self.public_constraint_name):
            qstr += f"@{name}: [{public_constraint[idx]}, {public_constraint[idx]}] "

        q = Query(qstr)

        try:
            result = self.r.ft('job').search(q)
            if result.total == 0:
                return False
        except Exception as e:
            self.logger.print(e, ERROR)
            return False

        for doc in result.docs:
            id = doc.id.split(':')[1]
            constraints_job_list.append(id)
            job_dict = json.loads(doc.json)["job"]
            job_total_demand_map[id] = job_dict["total_demand"]
            job_time_map[id] = job_dict['timestamp']
        constraints_job_list.sort(
            key=lambda x: (
                job_total_demand_map[x],
                job_time_map[x]))

        return True

    def irs_update_score(
            self,
            job_id: int,
            groupsize: int,
            idx: int,
            denominator: float,
            irs_epsilon: float = 0,
            std_round_time: float = 0):
        """Calculate job score using IRS.

        Args:
            job: job id
            groupsize: number of jobs in a group with the same constraints
            idx: index of the job within the group list
            denominator: IRS score denominator, eligible client group size for the job group
            irs_epsilon: hyperparameter for fairness adjustment
            std_round_time: default round execution time for jobs that don't have history round info
        """

        score = (groupsize - idx) / denominator
        if irs_epsilon > 0:
            sjct = self._get_est_JCT(job_id, std_round_time)
            score = score * (self._get_job_time(job_id) / sjct)**irs_epsilon
        try:
            self.r.execute_command(
                'JSON.SET', f"job:{job_id}", "$.job.score", score)
            self.logger.print(f"-------job:{job_id} {score:.3f} ", INFO)
        except Exception as e:
            self.logger.print(e, ERROR)

    def fifo_update_all_job_score(self):
        """Give every job which doesn't have a score yet a score of -timestamp

        Returns:
            boolean indicating whether there is a score updated
        """
        q = Query('@score: [0, 0]')
        try:
            result = self.r.ft('job').search(q)
        
            if result.total == 0:
                return
            for doc in result.docs:
                id = doc.id
                job_time = json.loads(doc.json)["job"]["timestamp"]
                score  = -(job_time - self.start_time)
                self.logger.print(f"-------{id} {score:.3f} ", INFO)
                self.r.execute_command('JSON.SET', id, "$.job.score", score)
        except Exception as e:
            self.logger.print(e, ERROR)

    def random_update_all_job_score(self):
        """Do not assign score to jobs. Instead, client will recieved a randomly shuffled offer list
        """
        pass

    def srsf_update_all_job_score(self):
        """Give every job a score of -remaining demand

            remaining demand = est total demand - attained demand
            Prioritize job with the smallest remaining demand.
        """
        try:
            q = Query('*')
            result = self.r.ft('job').search(q)
            if result.total == 0:
                return
            for doc in result.docs:
                id = doc.id
                job_dict = json.loads(doc.json)['job']
                remain_demand = max(job_dict['total_demand'] - job_dict['attained_service'], 0)
                score = -remain_demand
                self.logger.print(f"-------{id} {score:.3f} ", INFO)
                self.r.execute_command('JSON.SET', id, "$.job.score", score)
        except Exception as e:
            self.logger.print(e, ERROR)

    def srtf_update_all_job_score(self, std_round_time: float):
        """Give every job a score of -remaining time
            remaining time = past avg round time * remaining round
            Prioritize job with the shortest remaining demand
        """
        try:
            q = Query('*')
            result = self.r.ft('job').search(q)
            if result.total == 0:
                return
            for doc in result.docs:
                id = doc.id
                job_dict = json.loads(doc.json)['job']
                past_round = job_dict['round']
                runtime = time.time() - job_dict['timestamp']
                avg_round_time = runtime / past_round if past_round > 0 else std_round_time
                    
                if job_dict['total_round'] > 0:
                    remain_round = max(job_dict['total_round'] - job_dict['round'], 0)
                    remain_time = remain_round * avg_round_time
                else:
                    remain_time = runtime

                score = -remain_time
                self.logger.print(f"-------{id} {score:.3f} ", INFO)
                self.r.execute_command('JSON.SET', id, "$.job.score", score)
        except Exception as e:
            self.logger.print(e, ERROR)

    def las_update_all_job_score(self):
        """Give every job a score of -attained service.
        """
        try:
            q = Query('*')
            result = self.r.ft('job').search(q)
            if result.total == 0:
                return
            for doc in result.docs:
                id = doc.id
                job_dict = json.loads(doc.json)['job']
                attained_service = job_dict['attained_service']
                score = -attained_service
                self.logger.print(f"-------{id} {score:.3f} ", INFO)
                self.r.execute_command('JSON.SET', id, "$.job.score", score)
        except Exception as e:
            self.logger.print(e, ERROR)

    def _get_job_time(self, job_id: int) -> float:
        id = f"job:{job_id}"
        try:
            timestamp = float(self.r.json().get(id, "$.job.timestamp")[0])
            return time.time() - timestamp
        except Exception as e:
            self.logger.print(e, WARNING)
            return 0

    def _get_est_JCT(self, job_id: int, std_round_time: float) -> float:
        id = f"job:{job_id}"
        try:
            start_time = float(self.r.json().get(job_id, "$.job.timestamp")[0])
            round_executed = int(self.r.json().get(job_id, "$.job.round")[0])
            runtime = time.time() - start_time
            avg_round_time = runtime / round_executed if round_executed > 0 else std_round_time
        
            total_round = int(self.r.json().get(id, ".job.total_round")[0])
            if total_round > 0:
                est_jct = runtime + max(total_round - round_executed, 0) * avg_round_time
            else:
                est_jct = 2 * runtime
            return est_jct
            
        except Exception as e:
            self.logger.print(e, WARNING)
            return 1000 * std_round_time


class SC_client_db_portal(Client_db):
    def __init__(self, gconfig, logger):
        """Initialize client db portal

        Args:
            gconfig: config dictionary
                public_max: upper bound of the score
                client_manager: list of client manager address
                    ip:
                    client_db_port
                client_expire_time: expiration time of clients in the db
                job_public_constraint: name of public constraint
            logger
        """

        # TODO determine which client db to connect, by default db 0
        super().__init__(gconfig, 0, False, logger)
        self.public_max = gconfig['public_max']

    def get_client_size(self) -> int:
        """Get client dataset size
        """
        num = 0
        try:
            info = self.r.ft('client').info()
            num = int(info['num_docs'])
        except Exception as e:
            self.logger.print(e, ERROR)

        return num

    def get_client_proportion(self, public_constraint: tuple) -> float:
        """Get client subset size

        Args:
            public_constraint: lower bounds of the client specification.
                                Every client in the returned subset has
                                spec greater or equal to this constraint
        """

        client_size = self.get_client_size()
        if client_size == 0:
            return 0.01

        qstr = ""
        for idx, name in enumerate(self.public_constraint_name):
            qstr += f"@{name}: [{public_constraint[idx]}, {self.public_max[name]}] "

        size = 0
        try:
            q = Query(qstr).no_content()
            size = int(self.r.ft('client').search(q).total)
        except Exception as e:
            self.logger.print(e, ERROR)

        if size == 0:
            return 0.01

        return size / client_size

    def get_irs_denominator(self, client_size: int, q: str) -> float:
        """Get IRS denominator value using client subset size which is defined by input query

        Args:
            client_size: total number of client
            q: query which defines a client subset
        """
        if client_size == 0:
            return 0.01
        size = 0
        q = Query(q).no_content()
        try:
            size = int(self.r.ft('client').search(q).total)
        except Exception as e:
            self.logger.print(e, ERROR)

        if size == 0:
            return 0.01

        return size / client_size
