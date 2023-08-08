from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import pickle
import grpc
import time
from datetime import datetime

#TODO state flow check
#TODO add value check

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

def get_time() -> str:
    current_time = datetime.now()
    format_time = current_time.strftime("%Y-%m-%d:%H:%M:%S:%f")[:-4]
    return format_time

def encode_specification(**kargs) -> tuple[list, list]:
    pass

def gen_client_config():
    pass

class Propius_job():
    def __init__(self, client_config: dict, verbose: bool = False):
        self.id = -1
        try:
            # TODO arguments check
            # TODO add state flow check
            self.public_specifications = tuple(client_config['public_specifications'])
            self.private_specifications = tuple(client_config['private_specifications'])
            
            self._lb_ip = client_config['load_balancer_ip']
            self._lb_port = client_config['load_balancer_port']
            self._lb_channel = None
            self._lb_stub = None

            self.verbose = verbose
        except BaseException:
            raise ValueError("Missing config arguments")
        
    def _cleanup_routine(self):
        try:
            self._lb_channel.close()
        except BaseException:
            pass

    def __del__(self):
        self._cleanup_routine()

    def _connect_lb(self) -> None:
        self._lb_channel = grpc.insecure_channel(f'{self._lb_ip}:{self._lb_port}')
        self._lb_stub = propius_pb2_grpc.Load_balancerStub(self._lb_channel)

        if self.verbose:
            print(f"{get_time()} Client: connecting to load balancer at {self._lb_ip}:{self._lb_port}")

    def connect(self, num_trial: int=1):
        """Connect to Propius load balancer

        Raise:
            RuntimeError: if can't establish connection after multiple trial
        """
        for _ in range(num_trial):
            try:
                self._connect_lb()
                if self.verbose:
                    print(f"{get_time()} Client: connected to Propius")
                return
            except Exception as e:
                if self.verbose:
                    print(f"{get_time()} {e}")
                time.sleep(2)

        raise RuntimeError(
            "Unable to connect to Propius at the moment")
    
    def client_check_in(self, num_trial: int=1) -> tuple[list, list]:
        
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
                if self.verbose:
                    print(f"{get_time()} Client {self.id}: checked in to Propius")
                return (task_ids, task_private_constraint)
            
            except Exception as e:
                if self.verbose:
                    print(f"{get_time()} {e}")
                time.sleep(2)
        raise RuntimeError("Unable to connect to Propius at the moment")
    
    def client_ping(self, num_trial: int=1) -> tuple[list, list]:

        for _ in range(num_trial):
            try:
                cm_offer = self._lb_stub.CLIENT_PING(propius_pb2.client_id(id=self.id))
                task_ids = pickle.loads(cm_offer.task_offer)
                task_private_constraint = pickle.loads(
                    cm_offer.private_constraint)
                if self.verbose:
                    print(f"{get_time()} Client {self.id}: pinged Propius")
                return (task_ids, task_private_constraint)
            
            except Exception as e:
                if self.verbose:
                    print(f"{get_time()} {e}")
                time.sleep(2)
        
        raise RuntimeError("Unable to connect to Propius at the moment")
    
    def select_task(self, task_ids: list, private_constraints: list)->int:

        for idx, task_id in enumerate(task_ids):
            if len(
                    self.private_specifications) != len(
                    private_constraints[idx]):
                raise ValueError(
                    "client private specification len does not match required")
            if geq(self.private_specifications, private_constraints[idx]):
                if self.verbose:
                    print(f"{get_time()} Client {self.id}: select task {task_id}")
                return task_id

        if self.verbose: 
            print(f"{get_time()} Client {self.id}: not eligible")
        return -1
    
    def client_accept(self, task_id: int, num_trial: int)->bool:
        for _ in range(num_trial):
            client_accept_msg = propius_pb2.client_accept(
                client_id=self.id, task_id=task_id
            )
            try:
                cm_ack = self._lb_stub.CLIENT_ACCEPT(client_accept_msg)
                if self.verbose:
                    if cm_ack.ack:
                        print(f"{get_time()} Client {self.id}: client task selection is recieved")
                    else:
                        print(f"{get_time()} Client {self.id}: client task selection is rejected")
                return cm_ack.ack
    
            except Exception as e:
                if self.verbose:
                    print(f"{get_time()} {e}")
                time.sleep(2)
        
        raise RuntimeError("Unable to connect to Propius at the moment")

    


