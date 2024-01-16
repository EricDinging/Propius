"""Aggregation store base module."""

from propius.parameter_server.module.commons import Entry
from propius.parameter_server.module.reduce import base_reduce
import copy
import asyncio
import torch


class Aggregation_store_entry(Entry):
    def __init__(self):
        super().__init__()
        self.agg_cnt = 0

    def __str__(self):
        return super().__str__() + f", agg_cnt: {self.agg_cnt}"

    def increment_agg_cnt(self, cnt: int):
        self.agg_cnt += copy.deepcopy(cnt)

    def get_agg_cnt(self):
        return self.agg_cnt


class Aggregation_store:
    def __init__(self):
        self.store_dict = {}
        self.lock = asyncio.Lock()

    async def get_key(self):
        async with self.lock:
            return copy.deepcopy(self.store_dict.keys())

    async def set_entry(self, job_id: int, entry: Aggregation_store_entry):
        async with self.lock:
            self.store_dict[job_id] = entry

    async def get_entry(self, job_id: int):
        async with self.lock:
            return copy.deepcopy(self.store_dict.get(job_id))

    async def clear_entry(self, job_id: int):
        async with self.lock:
            entry: Aggregation_store_entry = self.store_dict.pop(job_id, None)
            if entry:
                entry.clear()

    async def update(self, job_id: int, round: int, agg_cnt: int, data, meta={}) -> bool:
        async with self.lock:
            entry: Aggregation_store_entry = self.store_dict.get(job_id)
            if entry:
                if entry.get_round() == round:
                    entry.increment_agg_cnt(agg_cnt)
                    if entry.param:
                        base_reduce(entry.param, data, torch.Tensor.add_)
                    else:
                        entry.set_param(data)
                    return True
                elif entry.get_round() > round:
                    return False

            new_agg_entry = Aggregation_store_entry()
            new_agg_entry.set_config(meta)
            new_agg_entry.set_round(round)
            new_agg_entry.set_param(data)
            self.store_dict[job_id] = new_agg_entry
            return True

    async def fetch(self) -> dict:
        async with self.lock:
            result = self.store_dict
            self.store_dict = {}
            return result

    def __str__(self):
        s = ""
        for key, entry in self.store_dict.items():
            s += f"job_id: {key}, " + entry.__str__() + "\n"
        return s
