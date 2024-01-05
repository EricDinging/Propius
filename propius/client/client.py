from propius.controller.client import Propius_client
from propius.parameter_server.client import Propius_ps_client
import time


class Client:
    def __init__(self, config: dict, verbose: bool = False, logging: bool = False):
        self.client_controller = Propius_client(config, verbose, logging)

        self.client_ps = None
        self.id = -1
        self.config = config
        self.verbose = verbose
        self.logging = logging

        self.task_id = -1

    def fetch(self, timeout=60):
        start_time = time.time()

        while True:
            task_ids, task_private_constraint = [], []
            task_ids, task_private_constraint = self.client_controller.client_check_in()
            self.id = self.client_controller.id
            self.client_ps = Propius_ps_client(
                self.config, self.id, self.verbose, self.logging
            )

            ttl = 5
            while not task_ids:
                if time.time() - start_time > timeout or ttl <= 0:
                    break

                time.sleep(2)
                ttl -= 1
                task_ids, task_private_constraint = self.client_controller.client_ping()

            if task_ids:
                task_id = self.client_controller.select_task(
                    task_ids, task_private_constraint
                )

                if task_id >= 0:
                    result = self.client_controller.client_accept(task_id)
                    if result:
                        round = result[2]
                        code, meta, data = self.client_ps.get(task_id, round)

                        if code == 1:
                            return (meta, data)

            time.sleep(2)
            if time.time() - start_time > timeout:
                break
        return None
            
