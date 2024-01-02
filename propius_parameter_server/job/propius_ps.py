from propius_parameter_server.channels import (
    parameter_server_pb2,
    parameter_server_pb2_grpc,
)
import pickle
import grpc
import time


class Propius_ps_job:
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

    def put(self, round: int, demand: int, meta, data):
        meta["demand"] = demand
        put_msg = parameter_server_pb2.job(
            code = 5,
            job_id = self.id,
            round = round,
            meta = pickle.dumps(meta),
            data = pickle.dumps(data)
        )

        return_msg = self._ps_stub.JOB_PUT(put_msg)
        return True if return_msg.code == 1 else False
    
    def get(self, round: int):
        get_msg = parameter_server_pb2.job(
            code = 0,
            job_id = self.id,
            round = round,
            meta = pickle.dumps(""),
            data = pickle.dumps("")
        )

        result = self._ps_stub.JOB_GET(get_msg)
        return (
            result.code,
            pickle.loads(result.meta),
            pickle.loads(result.data) 
        )
    
    def delete(self):
        delete_msg = parameter_server_pb2.job(
            code = 0,
            job_id = self.id,
            round = -1,
            meta = pickle.dumps(""),
            data = pickle.dumps("")
        )
        self._ps_stub.JOB_DELETE(delete_msg)
