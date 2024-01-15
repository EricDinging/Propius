"""Leaf parameter server"""

from propius.parameter_server.util import Msg_level, Propius_logger
from propius.parameter_server.module.parameter_store.base import (
    Parameter_store_entry,
    Parameter_store,
)
from propius.parameter_server.module.aggregation_store.base import (
    Aggregation_store_entry,
    Aggregation_store,
)

import pickle
from propius.parameter_server.channels import (
    parameter_server_pb2,
    parameter_server_pb2_grpc,
)
import asyncio
import grpc


class Parameter_server:
    def __init__(self, gconfig, logger):
        self.aggregation_store = Aggregation_store()
        self.parameter_store = Parameter_store(gconfig["leaf_parameter_store_ttl"])
        self.gconfig = gconfig
        self.logger: Propius_logger = logger

        self._root_ps_ip = gconfig["root_ps_ip"]
        self._root_ps_port = gconfig["root_ps_port"]
        self._root_ps_channel = None
        self._root_ps_stub = None

        self._connect_root_ps()

    def _cleanup_routine(self):
        try:
            self._root_ps_channel.close()
        except Exception:
            pass

    def __del__(self):
        self._cleanup_routine()

    def _connect_root_ps(self):
        try:
            self._root_ps_channel = grpc.insecure_channel(
                f"{self._root_ps_ip}:{self._root_ps_port}"
            )
            self._root_ps_stub = parameter_server_pb2_grpc.Parameter_serverStub(
                self._root_ps_channel
            )

            self.logger.print(
                f"connected to root ps at {self._root_ps_ip}:{self._root_ps_port}",
                Msg_level.INFO,
            )
        except Exception as e:
            self.logger.print(e, Msg_level.ERROR)
    
    async def _new_param(self, job_id: int, round: int, root_return_msg):
        #FIXTHIS should just upload
        await self.aggregation_store.clear_entry(job_id)
        
        await self.parameter_store.clear_entry(job_id)

        data = pickle.loads(root_return_msg.data)
        meta = pickle.loads(root_return_msg.meta)
        new_entry = Parameter_store_entry()
        new_entry.set_config(meta)
        new_entry.set_param(data)
        new_entry.set_round(round)
        await self.parameter_store.set_entry(job_id, new_entry)

        new_agg_entry = Aggregation_store_entry()
        new_agg_entry.set_config(meta)
        new_agg_entry.set_round(round)
        new_agg_entry.set_param(data)
        await self.aggregation_store.set_entry(job_id, new_agg_entry)

    async def CLIENT_GET(self, request, context):
        job_id, round = request.job_id, request.round
        self.logger.print(
            f"receive client GET request, job_id: {job_id}, round: {round}",
            Msg_level.INFO,
        )

        entry: Parameter_store_entry = await self.parameter_store.get_entry(job_id)

        return_msg = parameter_server_pb2.job(
            code=3,
            job_id=-1,
            round=-1,
            meta=pickle.dumps({}),
            data=pickle.dumps([]),
        )

        if entry:
            entry_round = entry.get_round()
            if entry_round == round:
                # cache hit
                self.logger.print(entry, Msg_level.INFO)
                return_msg = parameter_server_pb2.job(
                    code=1,
                    job_id=job_id,
                    round=entry_round,
                    meta=pickle.dumps({}),
                    data=pickle.dumps(entry.get_param()),
                )
                return return_msg
            elif entry_round > round:
                # reqeusting old data
                return return_msg

        # cache miss

        get_msg = parameter_server_pb2.job(
            code=0,
            job_id=job_id,
            round=round,
            meta=pickle.dumps({}),
            data=pickle.dumps([]),
        )
        try:
            root_return_msg = self._root_ps_stub.CLIENT_GET(get_msg)
            self.logger.print(
                f"cache miss, fetch from root for job {job_id} round {round}",
                Msg_level.INFO,
            )
            return_msg = root_return_msg

            if root_return_msg.code == 1:
                # new parameter data
                await self._new_param(job_id, round, root_return_msg)

        except Exception as e:
            self.logger.print(e, Msg_level.ERROR)

        return return_msg