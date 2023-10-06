import redis
from redis.commands.json.path import Path
from redis.commands.search.query import Query
import time
import json
from propius.database import Temp_client_db
import random
from propius.util import Msg_level, Propius_logger, geq, Job_group, Group_condtition
import ast

class CM_temp_client_db_portal(Temp_client_db):
    def __init__(self, gconfig, cm_id: int, logger: Propius_logger):
        """Initialize temp client db portal

        Args:
            gconfig: config dictionary
                client_manager: list of client manager address
                    ip:
                    client_db_port
                client_expire_time: expiration time of clients in the db
                job_public_constraint: name of public constraint

            cm_id: id of the client manager is the user is client manager
            is_cm: bool indicating whether the user is client manager
            logger
        """

        super().__init__(gconfig, cm_id, True, logger)
        self.job_group = Job_group()
        self.max_task_len = gconfig['max_task_offer_list_len']

        #TODO hardcode
        q = ""
        for i, name in enumerate(self.public_constraint_name):
            q += f"@{name}: [0, {self.public_max[i]}]"
        cst = (0, 0, 0, 0)
        self.job_group.insert(cst, [0, 1])
        self.job_group[cst].insert_condition_and(q)

    def client_assign(self):
        for cst, job_list in self.job_group.cst_job_group_map:
            condition_q = self.job_group[cst].str()
            q = Query(condition_q)
            
            result = self.r.ft('client').search(q)
            job_list = job_list[:self.max_task_len]
            if result:
                for doc in result.docs:
                    client = json.loads(doc.json)
                    client['client']['job_ids'] = str(job_list)

                    modified_client_json_str = json.dumps(client)
                    doc.json = modified_client_json_str

    def insert(self, id: int, specifications: tuple):
        """Insert client metadata to database, set expiration time and start time

        Args:
            id
            specification: a tuple of public spec values
        """

        if len(specifications) != len(self.public_constraint_name):
            self.logger.print("Specification length does not match required", Msg_level.ERROR)
        client_dict = {"job_ids": "[]"}
        spec_dict = {self.public_constraint_name[i]: specifications[i]
                     for i in range(len(specifications))}
        client_dict.update(spec_dict)
        client = {
            "client": client_dict
        }
        try:
            self.r.json().set(f"client:{id}", Path.root_path(), client)
            self.r.expire(f"client:{id}", self.client_exp_time)
        except Exception as e:
            self.logger.print(e, Msg_level.ERROR)

    def get_task_id(self, client_id: int)->list:
        """Return task id of client id.
        
        Args: 
            client_id

        Returns: 
            a list of task id
        """

        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"client:{client_id}"
                    pipe.watch(id)
                    task_ids_str = str(self.r.json().get(id, "$.client.job_ids")[0])
                    pipe.unwatch()
                    task_list = ast.literal_eval(task_ids_str)
                    return task_list
                except redis.WatchError:
                    pass
                except Exception as e:
                    self.logger.print(e, Msg_level.ERROR)
                    return []

    def remove_client(self, client_id: int):
        """Remove the temp client from database. 

        Args:
            client_id
        """

        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"client:{client_id}"
                    pipe.watch(id)
                    pipe.delete(id)
                    pipe.unwatch()
                    self.logger.print(f"Remove client:{client_id}", Msg_level.WARNING)
                    return
                except redis.WatchError:
                    pass
                except Exception as e:
                    self.logger.print(e, Msg_level.ERROR)
                    return

    