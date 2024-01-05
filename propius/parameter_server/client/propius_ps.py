from propius.parameter_server.channels import (
    parameter_server_pb2,
    parameter_server_pb2_grpc,
)
from propius.parameter_server.util.commons import Msg_level, get_time
import pickle
import grpc
import time
import logging


class Propius_ps_client:
    def __init__(self, config, id=0, verbose: bool = False, logging: bool = False):
        """Init Propius_ps_client class

        Args:
            config:
                root_ps_ip
                root_ps_port
            id: client_id received from client_manager
            verbose: whether to print or not
            logging: whether to log or not
        Raises:
            ValueError: missing config args
        """
        try:
            self.id = id
            self._ps_ip = config["root_ps_ip"]
            self._ps_port = config["root_ps_port"]
            self._ps_channel = None
            self._ps_stub = None

            self.verbose = verbose
            self.logging = logging
        except Exception:
            raise ValueError("Missing config arguments")

    def _cleanup_routine(self):
        try:
            self._ps_channel.close()
        except Exception:
            pass

    def _custom_print(self, message: str, level: int = Msg_level.PRINT):
        if self.verbose:
            print(f"{get_time()} {message}")
        if self.logging:
            if level == Msg_level.DEBUG:
                logging.debug(message)
            elif level == Msg_level.INFO:
                logging.info(message)
            elif level == Msg_level.WARNING:
                logging.warning(message)
            elif level == Msg_level.ERROR:
                logging.error(message)

    def __del__(self):
        self._cleanup_routine()

    def _connect_ps(self) -> None:
        self._ps_channel = grpc.insecure_channel(f"{self._ps_ip}:{self._ps_port}")
        self._ps_stub = parameter_server_pb2_grpc.Parameter_serverStub(self._ps_channel)

        self._custom_print(
            f"Client: {self.id}: connecting to parameter_server at {self._ps_ip}:{self._ps_port}",
            Msg_level.INFO,
        )

    def connect(self, num_trial: int = 1):
        """Connect to Propius parameter server

        Raise:
            RuntimeError: if can't establish connection after multiple trial
        """
        for _ in range(num_trial):
            try:
                self._connect_ps()
                return
            except Exception as e:
                self._custom_print(e, Msg_level.ERROR)
                time.sleep(5)

        raise RuntimeError("Unable to connect to Propius PS at the moment")

    def close(self):
        """Clean up allocation, close connection to Propius parameter server."""
        self._cleanup_routine()

    def get(self, job_id: int, round: int):
        """Get job metadata and data for a round. The call will only be successful if
        the job entry in parameter store matches the job_id and round input, and
        correct job config and parameter will be returned.

        Args:
            job_id: job id that the client is paired with
            round: round number that client partipates in

        Returns:
            code: 1 - successful, 2 - stale entry, 3 - error
            meta: metadata
            data: parameter

        Raises:
            RuntimeError: if can't send register request after multiple trial
        """
        get_msg = parameter_server_pb2.job(
            code=0,
            job_id=job_id,
            round=round,
            meta=pickle.dumps(""),
            data=pickle.dumps(""),
        )
        for _ in range(3):
            self.connect()
            try:
                return_msg = self._ps_stub.CLIENT_GET(get_msg)
                self._cleanup_routine()
                self._custom_print(
                    f"Client {self.id}: send GET request for job: {job_id} round: {round}",
                    Msg_level.INFO,
                )
                return (
                    return_msg.code,
                    pickle.loads(return_msg.meta),
                    pickle.loads(return_msg.data),
                )
            except Exception as e:
                self._custom_print(e, Msg_level.ERROR)
                self._cleanup_routine()
                time.sleep(5)
        raise RuntimeError("Unable to send get request to Propius PS at the moment")

    def push(self, job_id: int, round: int, data: list):
        """Push client local execution result (data) to Propius parameter server.
        Parameter server will try to aggregate (data) with the existing parameter on the server.
        If the corresponding job entry is updated, ttl for that entry will also be updated.

        Args:
            job_id: job id that the client targets
            round: round that the client participates in
            data: client local execution result

        Returns:
            code: 1 - success, 4 - entry not found

        Raises:
            RuntimeError: if can't send register request after multiple trial
        """
        push_msg = parameter_server_pb2.job(
            code=0,
            job_id=job_id,
            round=round,
            meta=pickle.dumps({"agg_cnt": 1}),
            data=pickle.dumps(data),
        )

        for _ in range(3):
            self.connect()
            try:
                return_msg = self._ps_stub.CLIENT_PUSH(push_msg)
                self._custom_print(
                    f"Client {self.id}: send PUSH request for job: {job_id} round: {round}"
                )
                self._cleanup_routine()
                return return_msg.code
            except Exception as e:
                self._custom_print(e, Msg_level.ERROR)
                self._cleanup_routine()
                time.sleep(5)
        raise RuntimeError("Unable to send push request to Propius PS at the moment")
