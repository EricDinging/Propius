"""Storage entry class."""

import copy
import uuid
from propius.parameter_server.config import (
    OBJECT_STORE_DIR
)
import pathlib

class Entry:
    def __init__(self, in_memory: bool = True):
        self.round_num = 0
        self.config = None
        self.param = None
        self.in_memory = in_memory
        
    def set_round(self, round: int):
        self.round_num = copy.deepcopy(round)

    def set_config(self, config):
        self.config = copy.deepcopy(config)

    def set_param(self, param):
        if self.in_memory:
            self.param = copy.deepcopy(param)
        else:
            self.param: pathlib.Path = OBJECT_STORE_DIR / str(uuid.uuid4()) + '.bin'
            with open(self.param, 'wb') as file:
                file.write(param)

    def get_round(self) -> int:
        return self.round_num
    
    def get_config(self):
        return self.config
    
    def get_param(self):
        if self.in_memory:
            return copy.deepcopy(self.param)
        else:
            with open(self.param, 'rb') as file:
                return file.read()
    
    def clear(self):
        if not self.in_memory and self.param.exists():
            self.param.unlink()
        self.config = None
        self.param = None

    def __str__(self):
        return (
            f"round_num: {self.round_num}, config: {self.config}"
        )
