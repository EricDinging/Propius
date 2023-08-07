import pickle
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import grpc
import time

def encode_constraints(**kargs)->tuple[list, list]:
    """Encode job constraints. Eg. encode_constraints(cpu=50, memory=50).
    Currently supported keys are {cpu, memory, os}

    Args:
        Keyword arguments 

    Raises: 
        ValueError: if input key is not recognized
    """

    public_constraint_dict = {
        "cpu": 0,
        "memory": 0,
        "os": 0,
    }
    private_constraint_dict = {}

    for key in public_constraint_dict.keys():
        if key in kargs:
            public_constraint_dict[key] = kargs[key]

    for key in private_constraint_dict.keys():
        if key in kargs:
            private_constraint_dict[key] = kargs[key]

    for key in kargs.keys():
        if key not in public_constraint_dict and key not in private_constraint_dict:
            raise ValueError(f"{key} constraint is not supported")
    
    #TODO encoding, value check

    return (list(public_constraint_dict.values()), list(private_constraint_dict))

def gen_job_config(constraint: tuple[list, list],
                   est_total_round: int,
                   demand: int,
                   job_manager_ip: str,
                   job_manager_port:int,
                   ps_ip: str,
                   ps_port: int
                   )->dict:
    #TODO
    pass

class Propius_job():
    def __init__(self, job_config):
        """Init Propius_job class

        Args:
            job_config:
                public_constraint
                private_constraint
                total_round
                demand
                job_manager_ip
                job_manager_port
                ip
                port
        """
        self.id = -1
        try:
            #TODO arguments check
            self.public_constraint = tuple(job_config['public_constraint'])
            self.private_constraint = tuple(job_config['private_constraint'])
            self.est_total_round = job_config['total_round']
            self.demand = job_config['demand']
            self.jm_ip = job_config['job_manager_ip']
            self.jm_port = job_config['job_manager_port']
            self._jm_channel = None
            self._jm_stub = None
            self.ip = job_config['ip']
            self.port = job_config['port']

        except:
            raise ValueError("Missing config arguments")
        
    def _cleanup_routine(self):
        try:
            self.jm_channel.close()
        except:
            pass
    
    def __del__(self):
        self._cleanup_routine()
        
        
    def _connect_jm(self, jm_ip: str, jm_port: int) -> None:
        self._jm_channel = grpc.insecure_channel(f'{jm_ip}:{jm_port}')
        self._jm_stub = propius_pb2_grpc.Job_managerStub(self.jm_channel)
        # print(f"Job {self.id}: connecting to job manager at {jm_ip}:{jm_port}") 

    def connect(self) -> None:
        """Connect to Propius job manager

        Raise:
            RuntimeError: if can't establish connection after multiple trial
        """
        for _ in range(10):
            try:
                self._connect_jm(self.jm_ip, self.jm_port)
                return
            except:
                time.sleep(2)

        raise RuntimeError("Unable to connect to Propius job manager at the moment")

    def close(self) -> None:
        """Clean up allocation, close connection to Propius job manager
        """
        self._cleanup_routine()

    def register(self) -> bool:
        """Register job. Send job config to Propius job manager. This configuration will expire
        in one week, which means the job completion time should be within one week.

        Raise:
            RuntimeError: if can't send register request after multiple trial
        """

        job_info_msg = propius_pb2.job_info(
            est_demand=self.demand,
            est_total_round=self.est_total_round,
            public_constraint=pickle.dumps(self.public_constraint),
            private_constraint=pickle.dumps(self.private_constraint),
            ip=pickle.dumps(self.ip),
            port=self.port,
        )

        for _ in range(10):
            try:
                ack_msg = self._jm_stub.JOB_REGIST(job_info_msg)
                self.id = ack_msg.id
                ack = ack_msg.ack
                if not ack:
                    # print(f"Job {self.id}: register failed")
                    return False
                else:
                    # print(f"Job {self.id}: register success")
                    return True
            except:
                time.sleep(2)

        raise RuntimeError("Unable to register to Propius job manager at the moment")
    
    def round_start_request(self, new_demand: bool, demand:int=0) -> bool:
        """Send round start request to Propius job manager. Client will be routed to parameter server after this call
        until the number of clients has reached specified demand, or round_end_request is called. 
        Note that though Propius provide the guarantee that the requested demand will be satisfied, 
        allocated clients may experience various issues such as network failure
        such that the number of check-in clients might be lower than what is demanded at the parameter server
        
        Args:
            new_demand: boolean indicating whether to use a new demand number for this round (only)
            demand: positive integer indicating number of demand in this round. 
                    If not specified, will use the default demand which is specified in the initial configuration

        Raise:
            RuntimeError: if can't send request after multiple trial
            ValueError: if input demand is not a positive integer
        """

        if not new_demand:
            this_round_demand = self.demand
        else:
            if demand <= 0:
                raise ValueError("Input demand number is not a positive integer")
            else:
                this_round_demand = demand

        request_msg = propius_pb2.job_round_info(
            id=self.id,
            demand=this_round_demand
        )
        
        for _ in range(10):
            try:
                ack_msg = self._jm_stub.JOB_REQUEST(request_msg)
                if not ack_msg.ack:
                    # print(
                    #     f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} request failed")
                    return False
                else:
                    # print(
                    #     f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} request success")
                    return True
            except:
                time.sleep(2)

        raise RuntimeError("Unable to send round start request to Propius job manager at the moment")
    
    def round_end_request(self) -> bool:
        """Send round end request to Propius job manager. Client won't be routed to parameter server after this call, 
        unless round_start_request is called

        Raise:
            RuntimeError: if can't send round end request after multiple trial
        """

        request_msg = propius_pb2.job_id(id=self.id)

        for _ in range(10):
            try:
                ack_msg = self._jm_stub.JOB_END_REQUEST(request_msg)
                if not ack_msg.ack:
                    # print(
                    #     f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} end request failed")
                    return False
                else:
                    # print(
                    #     f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} end request")
                    return True
            except:
                    time.sleep(2)
        
        raise RuntimeError("Unable to send round end request to Propius job manager at this moment")
    
    def complete_job(self):
        """Send complete job request to Propius job manager. Job configuration will be removed from Propius.
        
        Raise:
            RuntimeError: if can't send complete_job request after multiple trial
        """

        req_msg = propius_pb2.job_id(id=self.id)
        
        for _ in range(10):
            try:
                self._jm_stub.JOB_FINISH(req_msg)
                return
            
            except:
                time.sleep(2)

        raise RuntimeError("Unable to send complete job request to Propius job manager at this moment")