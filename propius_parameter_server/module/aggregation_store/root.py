"""Aggregation store root module."""

from propius_parameter_server.module.aggregation_store.base import (
    Aggregation_store_entry,
    Aggregation_store,
)
import copy
import asyncio


class Root_aggregation_store_entry(Aggregation_store_entry):
    def __init__(self):
        super().__init__()
        self.ttl = 2000
        self.demand = 0

    def __str__(self):
        return super().__str__() + f", ttl: {self.ttl}, demand: {self.demand}"

    def set_ttl(self, ttl: int):
        self.ttl = copy.deepcopy(ttl)

    def decrement_ttl(self) -> int:
        self.ttl -= 1
        return self.get_ttl()

    def get_ttl(self) -> int:
        return copy.deepcopy(self.ttl)

    def get_demand(self) -> int:
        return copy.deepcopy(self.demand)

    def set_demand(self, demand: int):
        self.demand = copy.deepcopy(demand)


class Root_aggregation_store(Aggregation_store):
    def __init__(self):
        super().__init__()

    async def set_entry(self, job_id: int, entry: Root_aggregation_store_entry):
        async with self.lock:
            self.store_dict[job_id] = entry

    async def get_entry_ref(self, job_id: int):
        return super().get_entry_ref(job_id)

    async def clear_entry(self, job_id: int):
        async with self.lock:
            entry: Root_aggregation_store_entry = self.store_dict.pop(job_id, None)
            if entry:
                entry.clear()

    def __str__(self):
        return super().__str__()

    async def clock_evict_routine(self):
        while True:
            async with self.lock:
                for key, entry in self.store_dict.items():
                    ttl = entry.decrement_ttl()
                    if ttl <= 0:
                        entry.clear()
                        self.store_dict.pop(key, None)
            await asyncio.sleep(1)
