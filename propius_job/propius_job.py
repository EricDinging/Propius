import pickle
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import grpc
import time

def gen_job_config(public_constraint: list,
                   private_constraint: list,
                   est_total_round: int,
                   demand: int,
                   job_manager_ip: str,
                   job_manager_port:int,
                   ps_ip: str,
                   ps_port: int
                   )->dict:
    pass

def encode_constraints(**kargs)->list:
    # os: 12.4 -> os: 66
    # cpu: None -> cpu: 0
    # return [66, 0]
    pass

class Propius_job():
    def __init__(self, job_config):
        self.id = -1
        try:
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
        
        # Connecting to Propius job manager server
        for _ in range(10):
            try:
                self._connect_jm(self.jm_ip, self.jm_port)
                return
            except:
                time.sleep(2)
        raise RuntimeError("Unable to connect to job manager")
    
    def _cleanup_routine(self):
        try:
            self.jm_channel.close()
        except:
            pass
    
    def __del__(self):
        try:
            self._cleanup_routine()
        except:
            pass
        
    def _connect_jm(self, jm_ip: str, jm_port: int) -> None:
        self._jm_channel = grpc.insecure_channel(f'{jm_ip}:{jm_port}')
        self._jm_stub = propius_pb2_grpc.Job_managerStub(self.jm_channel)
        # print(f"Job {self.id}: connecting to job manager at {jm_ip}:{jm_port}")   

    def register(self) -> bool:
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

        raise RuntimeError("Unable to register to Propius job manager")
    
    def round_start_request(self) -> bool:
        request_msg = propius_pb2.job_round_info(
            id=self.id,
            demand=self.demand,
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
        """optional, terminating request"""
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
        req_msg = propius_pb2.job_id(id=self.id)
        
        for _ in range(10):
            try:
                self._jm_stub.JOB_FINISH(req_msg)
                return
            
            except:
                time.sleep(2)

        raise RuntimeError("Unable to send complete job request to Propius job manager at this moment")