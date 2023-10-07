import redis
from redis.commands.json.path import Path
from redis.commands.search.query import Query
import time
import json
from propius.database import Temp_client_db
import random
from propius.util import Msg_level, Propius_logger, geq, Job_group
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

    def client_assign(self):
        for cst, job_list in self.job_group.cst_job_group_map.items():
            try:
                condition_q = self.job_group[cst].str()
                q = Query(condition_q)
                
                result = self.r.ft('temp').search(q)

                if result:
                    for doc in result.docs:
                        client_id = int(doc.id.split(':')[1])
                        self.r.json().set(f"temp:{client_id}", "$.temp.job_ids", str(job_list))
            except Exception:
                self.logger.print(e, Msg_level.ERROR)

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
            "temp": client_dict
        }
        try:
            self.r.json().set(f"temp:{id}", Path.root_path(), client)
            self.r.expire(f"temp:{id}", self.client_exp_time)
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
                    id = f"temp:{client_id}"
                    pipe.watch(id)
                    task_ids_str = str(self.r.json().get(id, "$.temp.job_ids")[0])
                    pipe.unwatch()
                    task_list = ast.literal_eval(task_ids_str)
                    return task_list
                except redis.WatchError:
                    pass
                except Exception as e:
                    return []

    def remove_client(self, client_id: int):
        """Remove the temp client from database. 

        Args:
            client_id
        """

        with self.r.json().pipeline() as pipe:
            while True:
                try:
                    id = f"temp:{client_id}"
                    pipe.watch(id)
                    pipe.delete(id)
                    pipe.unwatch()
                    self.logger.print(f"Remove temp client:{client_id}", Msg_level.WARNING)
                    return
                except redis.WatchError:
                    pass
                except Exception as e:
                    return

    