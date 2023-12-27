import redis
from redis.commands.json.path import Path
from redis.commands.search.query import Query
from propius_controller.database import Temp_client_db
from propius_controller.client_manager.cm_db_portal import CM_job_db_portal
from propius_controller.util import Msg_level, Propius_logger, geq, Job_group
import ast
import json
import random


class CM_temp_client_db_portal(Temp_client_db):
    def __init__(
        self,
        gconfig,
        cm_id: int,
        cm_job_db: CM_job_db_portal,
        logger: Propius_logger,
        flush: bool = False,
    ):
        """Initialize temp client db portal

        Args:
            gconfig: config dictionary
                client_manager: list of client manager address
                    ip:
                    client_db_port
                client_expire_time: expiration time of clients in the db
                job_public_constraint: name of public constraint
                flush: whether to flush the db first

            cm_id: id of the client manager is the user is client manager
            cm_job_db: job db portal
            is_cm: bool indicating whether the user is client manager
            logger
        """

        super().__init__(gconfig, cm_id, True, logger, flush)
        self.job_group = Job_group()
        self.assigned_ttl = self.client_exp_time / 2
        self.tier_num = gconfig["tier_num"] if "tier_num" in gconfig else 0
        self.job_db_portal = cm_job_db
        self.max_task_offer_list_len = gconfig["max_task_offer_list_len"]

    def update_job_group(self, new_job_group: Job_group):
        self.job_group = new_job_group

    def client_assign(self):
        """Assigning available job in job group to all clients in temporary datastore"""
        for key, job_list in self.job_group.key_job_group_map.items():
            try:
                condition_q = self.job_group[key].str()
                q = Query(condition_q).paging(0, 1000)
                result = self.r.ft("temp").search(q)

                self.logger.print(f"binding job group: {job_list}", Msg_level.INFO)

                def filter_key(job_id):
                    amount = self.job_db_portal.get_field(job_id, "amount")
                    demand = self.job_db_portal.get_field(job_id, "demand")
                    return amount < demand

                job_list = filter(filter_key, job_list)

                for doc in result.docs:
                    try:
                        client_id = doc.id
                        # get client attributes
                        temp_client = json.loads(doc.json)
                        client_attr_list = []
                        for name in self.public_constraint_name:
                            client_attr_list.append(float(temp_client["temp"][name]))
                        client_attr_tuple = tuple(client_attr_list)

                        assigned_job_list = []
                        for job_id in job_list:
                            if len(assigned_job_list) < self.max_task_offer_list_len:
                                if geq(
                                    client_attr_tuple,
                                    self.job_db_portal.get_job_constraints(job_id),
                                ):
                                    assigned_job_list.append(job_id)
                            else:
                                break
                        assigned_job_str = str(assigned_job_list)

                        self.logger.print(
                            f"bind client with job: {client_id} {assigned_job_str} ",
                            Msg_level.INFO,
                        )
                        self.r.execute_command("JSON.SET", client_id, "$.temp.job_ids", assigned_job_str)
                    except:
                        pass

            except Exception as e:
                self.logger.print(e, Msg_level.ERROR)

    def irs_client_assign(self):
        for key, job_list in self.job_group.key_job_group_map.items():
            try:
                condition_q = self.job_group[key].str()
                q = Query(condition_q).paging(0, 1000)
                result = self.r.ft("temp").search(q)

                job_list_str = str(job_list)

                self.logger.print(job_list_str, Msg_level.INFO)

                if self.tier_num > 1 and len(job_list) > 0 and len(result.docs) > 0:
                    front_job_id = job_list[0]
                    tier_lower_bound = [0 for _ in range(self.tier_num + 1)]
                    option_list = []
                    rem_job_list_str = str(job_list[1:])
                    for doc in result.docs:
                        try:
                            temp_client = json.loads(doc.json)
                            temp_client["temp"]["job_ids"] = rem_job_list_str
                            option_list.append(temp_client["temp"]["option"])
                        except:
                            pass

                    option_list.sort()
                    tier_len = int(len(option_list) / self.tier_num)
                    for i in range(self.tier_num):
                        tier_lower_bound[i] = option_list[i * tier_len]
                    tier_lower_bound[-1] = option_list[-1]

                    c = self.job_group.job_time_ratio_map[front_job_id]

                    u = random.randint(0, self.tier_num - 1)
                    gu = (
                        tier_lower_bound[0] / tier_lower_bound[u]
                        if tier_lower_bound[u] > 0
                        else 1
                    )

                    if self.tier_num + gu * c < c + 1:
                        self.logger.print(
                            f"Job {front_job_id} tier-matching, tier_num: {self.tier_num}"
                            f" u: {u}, gu: {gu}, c: {c}",
                            Msg_level.INFO,
                        )
                        for doc in result.docs:
                            try:
                                temp_client = json.loads(doc.json)
                                option = temp_client["temp"]["option"]
                                if (
                                    option >= tier_lower_bound[u]
                                    and option < tier_lower_bound[u + 1]
                                ):
                                    temp_client["temp"]["job_ids"] = job_list_str
                                else:
                                    temp_client["temp"]["job_ids"] = rem_job_list_str
                                self.r.json().set(doc.id, Path.root_path(), temp_client)
                                self.r.expire(doc.id, self.assigned_ttl)
                            except:
                                pass
                    else:
                        self.logger.print(
                            f"Job {front_job_id} not tier-matching,"
                            f"tier_num: {self.tier_num}"
                            f" u: {u}, gu: {gu}, c: {c}",
                            Msg_level.INFO,
                        )
                        for doc in result.docs:
                            try:
                                temp_client = json.loads(doc.json)
                                temp_client["temp"]["job_ids"] = job_list_str
                                self.r.json().set(doc.id, Path.root_path(), temp_client)
                                self.r.expire(doc.id, self.assigned_ttl)
                            except:
                                pass

                elif self.tier_num <= 1:
                    for doc in result.docs:
                        try:
                            temp_client = json.loads(doc.json)
                            temp_client["temp"]["job_ids"] = job_list_str
                            self.r.json().set(doc.id, Path.root_path(), temp_client)
                            self.r.expire(doc.id, self.assigned_ttl)
                        except:
                            pass

                    self.logger.print(
                        f"Insert job {job_list_str} to {len(result.docs)} clients",
                        Msg_level.INFO,
                    )

            except Exception as e:
                self.logger.print(e, Msg_level.ERROR)

    def insert(self, id: int, specifications: tuple, option: float = 0):
        """Insert client metadata to database, set expiration time and start time

        Args:
            id
            specification: a tuple of public spec values
            option: a optional value
        """

        if len(specifications) != len(self.public_constraint_name):
            self.logger.print(
                "Specification length does not match required", Msg_level.ERROR
            )
        client_dict = {"job_ids": "[]", "option": option}
        spec_dict = {
            self.public_constraint_name[i]: specifications[i]
            for i in range(len(specifications))
        }
        client_dict.update(spec_dict)
        client = {"temp": client_dict}
        try:
            self.r.json().set(f"temp:{id}", Path.root_path(), client)
            self.r.expire(f"temp:{id}", self.client_exp_time)
        except Exception as e:
            self.logger.print(e, Msg_level.ERROR)

    def get_task_id(self, client_id: int, specifications: tuple) -> list:
        """Return task id of client id.

        Args:
            client_id

        Returns:
            a list of task id
        """
        task_list = []
        try:
            id = f"temp:{client_id}"
            if self.r.execute_command("EXISTS", id):
                result = str(self.r.json().get(id, "$.temp.job_ids")[0])
                task_list = ast.literal_eval(result)

        except Exception as e:
            self.logger.print(e, Msg_level.ERROR)

        return task_list

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
                    self.logger.print(
                        f"Remove temp client:{client_id}", Msg_level.WARNING
                    )
                    return
                except redis.WatchError:
                    pass
                except Exception as e:
                    return
