from propius_parameter_server.channels import (
    parameter_server_pb2,
    parameter_server_pb2_grpc,
)
import pickle
import grpc
import time


class Propius_ps_client:
    def __init__(self, config, id=0):
        self.id = id

        self._ps_ip = config["root_ps_ip"]
        self._ps_port = config["root_ps_port"]
        self._ps_channel = None
        self._ps_stub = None

    def _cleanup_routine(self):
        try:
            self._ps_channel.close()
        except Exception:
            pass

    def __del__(self):
        self._cleanup_routine()

    def _connect_ps(self) -> None:
        self._ps_channel = grpc.insecure_channel(f"{self._ps_ip}:{self._ps_port}")
        self._ps_stub = parameter_server_pb2_grpc.Parameter_serverStub(self._ps_channel)

        print(f"connecting to parameter_server at {self._ps_ip}:{self._ps_port}")

    def connect(self, num_trial: int = 1):
        for _ in range(num_trial):
            try:
                self._connect_ps()
                return
            except Exception as e:
                print(e)
                time.sleep(2)

        raise RuntimeError("Unable to connect to Propius PS at the moment")

    def close(self):
        self._cleanup_routine()

    def get(self, job_id: int, round: int):
        get_msg = parameter_server_pb2.job(
            code = 0,
            job_id = job_id,
            round = round,
            meta = pickle.dumps(""),
            data = pickle.dumps("")
        )
        return_msg = self._ps_stub.CLIENT_GET(get_msg)

        return (
            return_msg.code,
            pickle.loads(return_msg.meta),
            pickle.loads(return_msg.data)
        )
    
    def push(self, job_id: int, round: int, data) -> bool:
        push_msg = parameter_server_pb2.job(
            code = 0,
            job_id = job_id,
            round = round,
            meta = pickle.dumps({"agg_cnt": 1}),
            data = pickle.dumps(data)
        )

        return_msg = self._ps_stub.CLIENT_PUSH(push_msg)

        return return_msg.code == 1
