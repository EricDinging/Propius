"""Aggregation store base module."""

from propius_parameter_server.module.commons import Entry
import copy
import asyncio


class Aggregation_store_entry(Entry):
    def __init__(self):
        super().__init__()
        self.agg_cnt = 0

    def __str__(self):
        return super().__str__() + f", agg_cnt: {self.agg_cnt}"

    def increment_agg_cnt(self):
        self.agg_cnt += 1

    def get_agg_cnt(self):
        return copy.deepcopy(self.agg_cnt)


class Aggregation_store:
    def __init__(self):
        self.store_dict = {}
        self.lock = asyncio.Lock()

    async def set_entry(self, job_id: int, entry: Aggregation_store_entry):
        async with self.lock:
            self.store_dict[job_id] = entry

    async def get_entry_ref(self, job_id: int):
        async with self.lock:
            return self.store_dict.get(job_id)

    async def clear_entry(self, job_id: int):
        async with self.lock:
            entry: Aggregation_store_entry = self.store_dict.pop(job_id, None)
            if entry:
                entry.clear()

    def __str__(self):
        s = ""
        for key, entry in self.store_dict:
            s += f"job_id: {key}, " + entry.__str__() + "\n"
        return s
