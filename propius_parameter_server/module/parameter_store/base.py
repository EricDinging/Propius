"""Aggregation store base module"""

from propius_parameter_server.module.commons import Entry
import copy
import asyncio


class Parameter_store_entry(Entry):
    def __init__(self):
        super().__init__()
        self.ttl = 100

    def __str__(self):
        return super().__str__() + f", ttl: {self.ttl}"

    def set_ttl(self, ttl: int):
        self.ttl = copy.deepcopy(ttl)

    def get_ttl(self):
        return copy.deepcopy(self.ttl)


class Parameter_store:
    def __init__(self):
        self.store_dict = {}
        self.lock = asyncio.Lock()

    async def set_entry(self, job_id: int, entry: Parameter_store_entry):
        async with self.lock:
            self.store_dict[job_id] = entry

    async def get_entry_ref(self, job_id: int):
        async with self.lock:
            return self.store_dict.get(job_id)

    async def clear_entry(self, job_id: int):
        async with self.lock:
            entry: Parameter_store_entry = self.store_dict.pop(job_id, None)
            if entry:
                entry.clear()

    async def clock_evict_routine(self):
        pass
