"""Storage entry class."""

import copy

class Entry:
    def __init__(self):
        self.round_num = 0
        self.config = None
        self.param = None

    def set_round(self, round: int):
        self.round_num = round

    def set_config(self, config):
        self.config = config

    def set_param(self, param):
        self.param = param

    def get_round(self) -> int:
        return self.round_num
    
    def get_config(self):
        return self.config
    
    def get_param(self):
        return self.param
    
    def clear(self):
        self.config = None
        self.param = None

    def __str__(self):
        return (
            f"round_num: {self.round_num}, config: {self.config}"
        )
