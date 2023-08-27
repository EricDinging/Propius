from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import pickle
import grpc
import time
from propius_client.commons import *
import logging

#TODO state flow check
#TODO add value check

def gen_client_config():
    pass

class Propius_client():
    def __init__(self, client_config: dict, verbose: bool = False, logging: bool = False):
        """Init Propius_client class

        Args:
            client_config:
                public_specifications: dict
                private_specifications: dict
                load_balancer_ip
                load_balancer_port
            verbose: whether to print or not
            logging: whether to log or not

        Raises:
            ValueError: missing config args
        """

        self.id = -1
        try:
            # TODO arguments check
            # TODO add state flow check
            public, private = encode_specs(**client_config['public_specifications'], **client_config['private_specifications'])
            self.public_specifications = tuple(public)
            self.private_specifications = tuple(private)
            
            self._lb_ip = client_config['load_balancer_ip']
            self._lb_port = client_config['load_balancer_port']
            self._lb_channel = None
            self._lb_stub = None

            self.verbose = verbose
            self.logging = logging
        except Exception:
            raise ValueError("Missing config arguments")
        
    def _cleanup_routine(self):
        try:
            self._lb_channel.close()
        except Exception:
            pass

    def __del__(self):
        self._cleanup_routine()

    def _custom_print(self, message: str, level: int=PRINT):
        if self.verbose:
            print(f"{get_time()} {message}")
        if self.logging:
            if level == DEBUG:
                logging.debug(message)
            elif level == INFO:
                logging.info(message)
            elif level == WARNING:
                logging.warning(message)
            elif level == ERROR:
                logging.error(message)
        
    def _connect_lb(self) -> None:
        self._lb_channel = grpc.insecure_channel(f'{self._lb_ip}:{self._lb_port}')
        self._lb_stub = propius_pb2_grpc.Load_balancerStub(self._lb_channel)

        self._custom_print(f"Client: connecting to load balancer at {self._lb_ip}:{self._lb_port}")

    def connect(self, num_trial: int=1):
        """Connect to Propius load balancer

        Args: 
            num_trial: number of connection attempt, default to 1

        Raise:
            RuntimeError: if can't establish connection after multiple trial
        """

        for _ in range(num_trial):
            try:
                self._connect_lb()
                self._custom_print(f"Client: connected to Propius")
                return
            except Exception as e:
                self._custom_print(e, ERROR)
                time.sleep(2)

        raise RuntimeError(
            "Unable to connect to Propius at the moment")
    
    def close(self) -> None:
        """Clean up allocation, close connection to Propius
        """

        self._cleanup_routine()
        self._custom_print(f"Client {self.id}: closing connection to Propius")

    def client_check_in(self, num_trial: int=1) -> tuple[list, list]:
        """Client check in. Send client public spec to Propius client manager. Propius will return task offer list for client to select a task locally.

        Args:
            num_trial: number of connection attempt, default to 1

        Returns:
            task_ids: list of task ids
            task_private_constraint: list of tuple of private constraint of the corresponding task in task_ids
        
        Raises: 
            RuntimeError: if can't establish connection after multiple trial
        """

        for _ in range(num_trial):
            client_checkin_msg = propius_pb2.client_checkin(
                public_specification=pickle.dumps(self.public_specifications)
            )
            try:
                cm_offer = self._lb_stub.CLIENT_CHECKIN(client_checkin_msg)
                self.id = cm_offer.client_id
                task_ids = pickle.loads(cm_offer.task_offer)
                task_private_constraint = pickle.loads(
                    cm_offer.private_constraint)
                
                self._custom_print(f"Client {self.id}: checked in to Propius, public spec {self.public_specifications}", INFO)
                return (task_ids, task_private_constraint)
            
            except Exception as e:
                self._custom_print(e, ERROR)
                time.sleep(2)
        raise RuntimeError("Unable to connect to Propius at the moment")
    
    def client_ping(self, num_trial: int=1) -> tuple[list, list]:
        """Client ping. Propius will return task offer list for client to select a task locally. Note that this function should only be called after client_check_in fails.

        Args:
            num_trial: number of connection attempt, default to 1

        Returns:
            task_ids: list of task ids
            task_private_constraint: list of tuple of private constraint of the corresponding task in task_ids
        
        Raises: 
            RuntimeError: if can't establish connection after multiple trial
        """

        for _ in range(num_trial):
            try:
                cm_offer = self._lb_stub.CLIENT_PING(propius_pb2.client_id(id=self.id))
                task_ids = pickle.loads(cm_offer.task_offer)
                task_private_constraint = pickle.loads(
                    cm_offer.private_constraint)
                self._custom_print(f"Client {self.id}: pinged Propius")
                return (task_ids, task_private_constraint)
            
            except Exception as e:
                self._custom_print(e, ERROR)
                time.sleep(2)
        
        raise RuntimeError("Unable to connect to Propius at the moment")
    
    def select_task(self, task_ids: list, private_constraints: list)->int:
        """Client select a task locally. The default strategy is to select the first task in task offer list of which the private constraint is satisfied by the client private specs. 

        Args:   
            task_ids: list of task id
            private_constraint: list of tuples of task private constraint

        Returns:
            task_id: id of task, -1 if no suitable task is found
        """

        for idx, task_id in enumerate(task_ids):
            if len(
                    self.private_specifications) != len(
                    private_constraints[idx]):
                raise ValueError(
                    "client private specification len does not match required")
            if geq(self.private_specifications, private_constraints[idx]):
                self._custom_print(f"Client {self.id}: select task {task_id}", INFO)
                return task_id

        self._custom_print(f"Client {self.id}: not eligible")
        return -1
    
    def client_accept(self, task_id: int, num_trial: int=1)->tuple[str, int]:
        """Client send task id of the selected task to Propius. Returns address of the selected job parameter server if successful, None otherwise

        Args:
            task_id: id of the selected task
            num_trial: number of connection attempt, default to 1

        Returns:
            ack: a boolean indicating whether the task selected is available for the client.
            ps_ip: ip address of the selected job parameter server
            ps_port: port number of the selected job parameter server
        Raises: 
            RuntimeError: if can't establish connection after multiple trial
        """

        for _ in range(num_trial):
            client_accept_msg = propius_pb2.client_accept(
                client_id=self.id, task_id=task_id
            )
            try:
                cm_ack = self._lb_stub.CLIENT_ACCEPT(client_accept_msg)
                if cm_ack.ack:
                    self._custom_print(f"Client {self.id}: client task selection is recieved")
                    return (pickle.loads(cm_ack.job_ip), cm_ack.job_port)
                else:
                    self._custom_print(f"Client {self.id}: client task selection is rejected", WARNING)
                    return None
            
            except Exception as e:
                self._custom_print(e, ERROR)
                time.sleep(2)
        
        raise RuntimeError("Unable to connect to Propius at the moment")

    def auto_assign(self, ttl:int=0)->tuple[int, bool, int, str, int]:
        """Automate client register, client ping, and client task selection process

        Args:
            ttl: number of attempts to inquire Propius for task offer until client is scheduled

        Returns:
            client_id: client id assigned by Propius
            status: a boolean indicating whether the client is assigned
            task_id: task id
            ps_ip: job parameter server ip address
            ps_port: job parameter server port address

        Raises:
            RuntimeError: if can't establish connection after multiple trial
        """

        task_ids, task_private_constraint = self.client_check_in()
        
        self._custom_print(
                f"Client {self.id}: recieve client manager offer: {task_ids}", INFO)
            
        while True:
            while ttl > 0:
                if len(task_ids) > 0:
                    break
                time.sleep(2)
                ttl -= 1
                task_ids, task_private_constraint = self.client_ping()
            
            task_id = self.select_task(task_ids, task_private_constraint)
            if task_id == -1:
                task_ids = []
                task_private_constraint = []
                if ttl <= 0:
                    return (self.id, False, -1, None, None)
                else:
                    continue

            result = self.client_accept(task_id)

            if not result:
                task_ids = []
                task_private_constraint = []
                if ttl <= 0:
                    return (self.id, False, -1, None, None)
                else:
                    continue
            else:
                self._custom_print(f"Client {self.id}: scheduled with {task_id}", INFO)
                break
        
        return (self.id, True, task_id, result[0], result[1])
    


