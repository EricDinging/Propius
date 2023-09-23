from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import pickle
import grpc
import time
import asyncio
from datetime import datetime
import logging
import math
from propius.util.commons import *
from propius.job.propius_job import Propius_job

class Propius_job_aio(Propius_job):

    async def _cleanup_routine(self):
            try:
                await self._jm_channel.close()
            except Exception:
                pass
    
    async def __del__(self):
        await self._cleanup_routine()

    def _connect_jm(self) -> None:
        self._jm_channel = grpc.aio.insecure_channel(f'{self._jm_ip}:{self._jm_port}')
        self._jm_stub = propius_pb2_grpc.Job_managerStub(self._jm_channel)

        self._custom_print(f"Job: connecting to job manager at {self._jm_ip}:{self._jm_port}", INFO)

    async def connect(self):
        """Connect to Propius job manager

        Raise:
            RuntimeError: if can't establish connection after multiple trial
        """
        for _ in range(3):
            try:
                self._connect_jm()
                return
            except Exception as e:
                self._custom_print(e, ERROR)
                await asyncio.sleep(5)

        raise RuntimeError(
            "Unable to connect to Propius job manager at the moment")
    
    async def close(self) -> None:
        """Clean up allocation, close connection to Propius job manager
        """
        
        await self._cleanup_routine()
        self._custom_print(f"Job {self.id}: closing connection to Propius", INFO)

    async def register(self) -> bool:
        """Register job. Send job config to Propius job manager. This configuration will expire
        in one week, which means the job completion time should be within one week.

        Returns:
            ack: status of job register

        Raise:
            RuntimeError: if can't send register request after multiple trial
        """

        job_info_msg = propius_pb2.job_info(
            est_demand=math.ceil(1.1 * self.demand),
            est_total_round=self.est_total_round,
            public_constraint=pickle.dumps(self.public_constraint),
            private_constraint=pickle.dumps(self.private_constraint),
            ip=pickle.dumps(self.ip),
            port=self.port,
        )
        for _ in range(3):
            await self.connect()
            try:
                ack_msg = await self._jm_stub.JOB_REGIST(job_info_msg)
                self.id = ack_msg.id
                ack = ack_msg.ack
                await self._cleanup_routine()
                if not ack:
                    if self.verbose:
                        self._custom_print(f"Job {self.id}: register failed", WARNING)
                    return False
                else:
                    if self.verbose:
                        self._custom_print(f"Job {self.id}: register success", INFO)
                    return True
            except Exception as e:
                if self.verbose:
                    self._custom_print(e, ERROR)
                await self._cleanup_routine()
                await asyncio.sleep(5)
                
        raise RuntimeError(
            "Unable to register to Propius job manager at the moment")
    
    async def start_request(self, new_demand: bool = False, demand: int = 0) -> bool:
        """Send start request to Propius job manager
        
        Client will be routed to parameter server after this call
        until the number of clients has reached specified demand, or end_request is called.
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
                raise ValueError(
                    "Input demand number is not a positive integer")
            else:
                this_round_demand = demand

        request_msg = propius_pb2.job_round_info(
            id=self.id,
            demand=this_round_demand
        )

        for _ in range(3):
            await self.connect()
            try:
                ack_msg = await self._jm_stub.JOB_REQUEST(request_msg)
                await self._cleanup_routine()
                if not ack_msg.ack:
                    self._custom_print(f"Job {self.id}: round request failed", WARNING)
                    return False
                else:
                    self._custom_print(f"Job {self.id}: round request succeeded", INFO)
                    return True
            except Exception as e:
                self._custom_print(e, ERROR)
                await self._cleanup_routine()
                await asyncio.sleep(5)

        raise RuntimeError(
            "Unable to send start request to Propius job manager at the moment")

    async def end_request(self) -> bool:
        """Send end request to Propius job manager. Client won't be routed to parameter server after this call,
        unless start_request is called

        Raise:
            RuntimeError: if can't send end request after multiple trial
        """

        request_msg = propius_pb2.job_id(id=self.id)

        for _ in range(3):
            await self.connect()
            try:
                ack_msg = await self._jm_stub.JOB_END_REQUEST(request_msg)
                await self._cleanup_routine()
                if not ack_msg.ack:
                    self._custom_print(f"Job {self.id}: end request failed", WARNING)
                    return False
                else:
                    self._custom_print(f"Job {self.id}: end request succeeded", INFO)
                    return True
            except Exception as e:
                self._custom_print(e, ERROR)
                await self._cleanup_routine()
                await asyncio.sleep(5)

        raise RuntimeError(
            "Unable to send end request to Propius job manager at this moment")

    async def complete_job(self):
        """Send complete job request to Propius job manager. Job configuration will be removed from Propius.

        Raise:
            RuntimeError: if can't send complete_job request after multiple trial
        """

        req_msg = propius_pb2.job_id(id=self.id)

        for _ in range(3):
            await self.connect()
            try:
                await self._jm_stub.JOB_FINISH(req_msg)
                await self._cleanup_routine()
                self._custom_print(f"Job {self.id}: job completed", WARNING)
                return
            except Exception as e:
                self._custom_print(e, ERROR)
                await self._cleanup_routine()
                await asyncio.sleep(5)

        raise RuntimeError(
            "Unable to send complete job request to Propius job manager at this moment")
    
    async def heartbeat(self):
        """Keep connection alive for long intervals during request
        """
        await self._jm_stub.HEART_BEAT(propius_pb2.empty())