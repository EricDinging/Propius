"""Parameter server base."""

from propius_parameter_server.module.aggregation_store.base import (
    Aggregation_store_entry,
    Aggregation_store
)
from propius_parameter_server.module.parameter_store.base import (
    Parameter_store_entry,
    Parameter_store
)
import asyncio

class Base_parameter_server:
    def __init__(self):
        self.parameter_store = Parameter_store()
        self.aggregation_store = Aggregation_store()

    async def GET(self, request, context):
        pass

    async def PUSH(self, request, context):
        pass