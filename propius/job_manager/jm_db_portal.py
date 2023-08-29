import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time
import json
from propius.database.db import *


class JM_job_db_portal(Job_db):
    def __init__(self, gconfig, logger):
        """Init job database portal class

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

        super().__init__(gconfig, True, logger)

    def register(
            self,
            job_id: int,
            public_constraint: tuple,
            private_constraint: tuple,
            job_ip: str,
            job_port: int,
            total_demand: int,
            total_round: int) -> bool:
        """Register incoming job to the database. 
        Return False if the job ID is already in the database. 
        Set expiration time of the job

        Args:
            job_id
            public_constraint: a tuple of values of constraints
            private_constraint: a tuple of values of constraints
            job_ip
            job_port
            total_demand
            total_round
        """

        if len(public_constraint) != len(self.public_constraint_name):
            raise ValueError("Public constraint len does not match required")
        if len(private_constraint) != len(self.private_constraint_name):
            raise ValueError("Private constraint len does not match required")

        job_dict = {
            "timestamp": time.time(),
            "total_sched": 0,
            "start_sched": 0,
            "ip": job_ip,
            "port": job_port,
            "total_demand": total_demand,
            "total_round": total_round,
            "round": 0,
            "demand": 0,
            "amount": 0,
            "score": 0,
        }
        constraint_dict = {"public_constraint":
                           {
                               self.public_constraint_name[i]: public_constraint[i]
                               for i in range(len(public_constraint))
                           },
                           "private_constraint":
                           {
                               self.private_constraint_name[i]: private_constraint[i]
                               for i in range(len(private_constraint))
                           },
                           }
        job_dict.update(constraint_dict)
        job = {
            "job": job_dict,
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
                    pipe.expire(f"job:{id}", self.job_exp_time)
                    pipe.unwatch()
                    return True
                except redis.WatchError:
                    pass
                except Exception as e:
                    self.logger.print(e, ERROR)
                    return False

    def request(self, job_id: int, demand: int) -> bool:
        """Update job metadata based on request. 
        Return False if the job_id is not in the database. 
        Increment job round, update job demand for new round, 
        and clear job allocation amount counter. Start sched_time counter

        Args:
            job_id
            demand
        """

        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"job:{job_id}"
                    pipe.watch(id)
                    if not pipe.get(id):
                        pipe.unwatch()
                        return False
                    cur_round = int(self.r.json().get(id, "$.job.round")[0])
                    total_round = int(
                        self.r.json().get(
                            id, "$.job.total_round")[0])
                    if cur_round >= total_round:
                        pipe.unwatch()
                        return False
                    pipe.multi()
                    pipe.execute_command(
                        'JSON.NUMINCRBY', id, "$.job.round", 1)
                    pipe.execute_command(
                        'JSON.SET', id, "$.job.demand", demand)
                    pipe.execute_command('JSON.SET', id, "$.job.amount", 0)
                    pipe.execute_command(
                        'JSON.SET', id, "$.job.start_sched", time.time())
                    pipe.execute()
                    return True
                except redis.WatchError:
                    pass
                except Exception as e:
                    self.logger.print(e, ERROR)
                    return False

    def end_request(self, job_id: int) -> bool:
        """Update job metadata based on end request. 
        Set job allocation amount as job demand to indicate allocation has finished. 
        Update total scheduling time.

        Args:
            job_id
        """

        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"job:{job_id}"
                    pipe.watch(id)
                    if not pipe.get(id):
                        pipe.unwatch(id)
                        return False
                    demand = int(self.r.json().get(id, "$.job.demand")[0])
                    amount = int(self.r.json().get(id, "$.job.amount")[0])
                    if amount >= demand:
                        pipe.unwatch()
                        return True
                    start_sched = float(
                        self.r.json().get(
                            id, "$.job.start_sched")[0])
                    pipe.multi()
                    pipe.execute_command(
                        'JSON.SET', id, "$.job.amount", demand)
                    sched_time = time.time() - start_sched
                    pipe.execute_command(
                        'JSON.NUMINCRBY', id, "$.job.total_sched", sched_time)
                    pipe.execute()
                    return True
                except redis.WatchError:
                    pass
                except Exception as e:
                    self.logger.print(e, ERROR)
                    return False

    def finish(self, job_id: int) -> tuple[tuple, int, int, float, float]:
        """Remove the job from database. 
        Returns a tuple of public constraints, demand, total round, 
        runtime and avg scheduling latency for analsis

        Args:
            job_id
        """

        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"job:{job_id}"
                    pipe.watch(id)
                    start_time = float(
                        self.r.json().get(
                            id, "$.job.timestamp")[0])
                    total_sched = float(
                        self.r.json().get(
                            id, "$.job.total_sched")[0])
                    round = float(self.r.json().get(id, "$.job.round")[0])
                    demand = int(self.r.json().get(id, "$.job.demand")[0])
                    total_round = int(
                        self.r.json().get(
                            id, "$.job.total_round")[0])

                    constraint_list = []
                    for name in self.public_constraint_name:
                        constraint_list.append(float(self.r.json().get(
                            id, f"$.job.public_constraint.{name}")[0]))
                    for name in self.private_constraint_name:
                        constraint_list.append(float(self.r.json().get(
                            id, f"$.job.private_constraint.{name}")[0]))

                    runtime = time.time() - start_time
                    sched_latency = total_sched / round if round > 0 else -1
                    pipe.delete(id)
                    pipe.unwatch()
                    return (
                        tuple(constraint_list),
                        demand,
                        total_round,
                        runtime,
                        sched_latency)
                except redis.WatchError:
                    pass
                except Exception as e:
                    self.logger.print(e, ERROR)
                    return (None, None, None, None, None)
