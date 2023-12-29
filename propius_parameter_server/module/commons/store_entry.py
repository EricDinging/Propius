"""Storage entry class."""

import copy

class Entry:
    def __init__(self):
        self.round_num = 0
        self.config = None
        self.param = None

    def increment_round(self):
        self.round_num += 1

    def set_config(self, config):
        self.config = copy.deepcopy(config)

    def set_param(self, param):
        self.param = copy.deepcopy(param)

    def get_round(self) -> int:
        return copy.deepcopy(self.round_num)
    
    def get_config(self):
        return copy.deepcopy(self.config)
    
    def get_param(self):
        return copy.deepcopy(self.param)
    
    def clear(self):
        self.config = None
        self.param = None

    def __str__(self):
        return (
            f"round_num: {self.round_num}, config: {self.config}"
        )
