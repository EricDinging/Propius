"""Root parameter server."""

from propius_parameter_server.util import Msg_level, Propius_logger
from propius_parameter_server.module.parameter_store.base import (
    Parameter_store_entry,
    Parameter_store,
)
from propius_parameter_server.module.aggregation_store.root import (
    Root_aggregation_store_entry,
    Root_aggregation_store,
)
import pickle
from propius_parameter_server.channels import parameter_server_pb2
from propius_parameter_server.channels import parameter_server_pb2_grpc
import asyncio


class Parameter_server:
    def __init__(self, gconfig, logger):
        self.aggregation_store = Root_aggregation_store()
        self.parameter_store = Parameter_store()

        self.gconfig = gconfig
        self.logger: Propius_logger = logger

    async def config(self):
        # FIXTHIS
        e = Parameter_store_entry()
        e.set_param("HELLO WORLD")
        await self.parameter_store.set_entry(0, e)
        self.logger.print(self.parameter_store)

    async def GET(self, request, context):
        job_id, round = request.job_id, request.round
        self.logger.print(
            f"receive GET request, job_id: {job_id}, round: {round}", Msg_level.INFO
        )

        entry: Parameter_store_entry = await self.parameter_store.get_entry_ref(job_id)

        return_msg = parameter_server_pb2.job(
            code=3,
            job_id=-1,
            round=-1,
            meta=pickle.dumps(""),
            data=pickle.dumps(""),
        )
        if entry:
            entry_round = entry.get_round()
            if entry_round == round:
                self.logger.print(entry, Msg_level.INFO)
                return_msg = parameter_server_pb2.job(
                    code=1,
                    job_id=job_id,
                    round=entry_round,
                    meta=pickle.dumps(""),
                    data=pickle.dumps(entry.get_param()),
                )
            elif entry_round < round:
                self.logger.print(f"job: {job_id} stale round {entry_round}, {round} expected")
                return_msg = parameter_server_pb2.job(
                    code=2,
                    job_id=job_id,
                    round=entry_round,
                    meta=pickle.dumps(""),
                    data=pickle.dumps(""),
                )
        return return_msg

    async def PUSH(self, request, context):
        pass
