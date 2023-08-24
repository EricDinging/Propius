import redis
from redis.commands.json.path import Path
import redis.commands.search.reducers as reducers
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query
import time
import json
from propius.util.commons import *


class Job_db:
    def __init__(self, gconfig, is_jm: bool):
        """Initialize job db portal

        Args:
            gconfig: config dictionary
                job_db_ip
                job_db_port
                sched_alg
                job_public_constraint: name of public constraint
                job_private_constraint: name of private constraint
                job_expire_time:
            is_jm: a bool indicating whether the user of the database is job manager
        """
        if gconfig['use_docker']:
            host = 'job_db'
            port = 6379
        else:
            host = gconfig['job_db_ip']
            port = int(gconfig['job_db_port'])
        self.r = redis.Redis(host=host, port=port)
        self.sched_alg = gconfig['sched_alg']
        self.gconfig = gconfig
        self.public_constraint_name = gconfig['job_public_constraint']
        self.private_constraint_name = gconfig['job_private_constraint']
    
        if is_jm:
            self.job_exp_time = gconfig['job_expire_time']
            schema = (
                NumericField(
                    "$.job.timestamp",
                    as_name="timestamp"),
                # job register time
                NumericField(
                    "$.job.total_sched",
                    as_name="total_sched"),
                # total amount of sched time
                NumericField(
                    "$.job.start_sched",
                    as_name="start_sched"),
                # last round start time
                TextField("$.job.ip", as_name="ip"),
                NumericField("$.job.port", as_name="port"),
                NumericField("$.job.total_demand", as_name="total_demand"),
                NumericField("$.job.total_round", as_name="total_round"),
                NumericField("$.job.round", as_name="round"),
                NumericField("$.job.demand", as_name="demand"),
                NumericField("$.job.amount", as_name="amount"),
                NumericField("$.job.score", as_name="score"),
            )

            schema = schema + tuple([NumericField(f"$.job.public_constraint.{name}", as_name=name)
                                     for name in self.public_constraint_name])

            schema = schema + tuple([NumericField(f"$.job.private_constraint.{name}", as_name=name)
                                     for name in self.private_constraint_name])

            try:
                self.r.ft("job").create_index(
                    schema, definition=IndexDefinition(
                        prefix=["job:"], index_type=IndexType.JSON))
            except Exception as e:
                custom_print(e, ERROR)
                pass

    def flushdb(self):
        self.r.flushdb()

    def get_job_size(self) -> int:
        info = self.r.ft('job').info()
        return int(info['num_docs'])


class Client_db:
    def __init__(self, gconfig, cm_id: int, is_cm: bool):
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
        if gconfig['use_docker']:
            host = f'client_db_{cm_id}'
            port = 6379
        else:
            host = gconfig['client_manager'][cm_id]['ip']
            port = gconfig['client_manager'][cm_id]['client_db_port']
        self.r = redis.Redis(host=host, port=port)
        self.start_time = int(time.time())
        self.client_exp_time = int(gconfig['client_expire_time'])

        self.public_constraint_name = gconfig['job_public_constraint']

        if is_cm:
            schema = (
                NumericField("$.client.timestamp", as_name="timestamp"),
            )

            schema = schema + tuple([NumericField(f"$.client.{name}", as_name=name)
                                    for name in self.public_constraint_name])

            try:
                self.r.ft("client").create_index(
                    schema, definition=IndexDefinition(
                        prefix=["client:"], index_type=IndexType.JSON))
            except BaseException:
                pass

    def flushdb(self):
        self.r.flushdb()


def geq(t1: tuple, t2: tuple) -> bool:
    """Compare two tuples. Return True only if every values in t1 is greater than t2

    Args:
        t1
        t2
    """

    for idx in range(len(t1)):
        if t1[idx] < t2[idx]:
            return False
    return True
