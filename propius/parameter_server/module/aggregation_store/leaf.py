"""Aggregation store leaf module"""

from propius.parameter_server.module.aggregation_store.base import (
    Aggregation_store_entry,
    Aggregation_store,
)
from propius.parameter_server.module.reduce import base_reduce
import copy
import asyncio
import torch

import pickle
from propius.parameter_server.channels import (
    parameter_server_pb2,
    parameter_server_pb2_grpc,
)


class Leaf_aggregation_store(Aggregation_store):
    def __init__(self, default_ttl: int = 5):
        super().__init__()
        self.default_ttl = default_ttl

    async def set_entry(self, job_id: int, entry: Aggregation_store_entry):
        async with self.lock:
            entry.set_ttl(self.default_ttl)
            self.store_dict[job_id] = entry

    async def get_entry(self, job_id: int):
        return await super().get_entry(job_id)

    async def clear_entry(self, job_id: int):
        return await super().clear_entry(job_id)

    async def update(
        self, job_id: int, round: int, agg_cnt: int, data, meta={}
    ) -> bool:
        async with self.lock:
            entry: Aggregation_store_entry = self.store_dict.get(job_id)
            if entry:
                if entry.get_round() == round:
                    entry.increment_agg_cnt(agg_cnt)
                    entry.set_ttl(self.default_ttl)
                    if entry.param:
                        base_reduce(entry.get_param(), data, torch.Tensor.add_)
                    else:
                        entry.set_param(data)
                    return True
                elif entry.get_round() > round:
                    return False

            new_agg_entry = Aggregation_store_entry()
            new_agg_entry.set_config(meta)
            new_agg_entry.set_round(round)
            new_agg_entry.set_param(data)
            new_agg_entry.set_ttl(self.default_ttl)
            new_agg_entry.increment_agg_cnt(agg_cnt)
            self.store_dict[job_id] = new_agg_entry
            return True

    async def clock_evict_routine(
        self, stub: parameter_server_pb2_grpc.Parameter_serverStub
    ):
        try:
            while True:
                async with self.lock:
                    for key in list(self.store_dict.keys()):
                        entry: Aggregation_store_entry = self.store_dict[key]
                        ttl = entry.decrement_ttl()
                        if ttl <= 0:
                            try:
                                push_msg = parameter_server_pb2.job(
                                    code=0,
                                    job_id=key,
                                    round=entry.get_round(),
                                    meta=pickle.dumps({"agg_cnt": entry.get_agg_cnt()}),
                                    data=pickle.dumps(entry.get_param()),
                                )
                                stub.CLIENT_PUSH(push_msg)
                            except Exception:
                                pass
                            entry.clear()
                            self.store_dict.pop(key, None)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    def __str__(self):
        return super().__str__()
