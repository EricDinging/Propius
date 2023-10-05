from datetime import datetime
from enum import Enum
import logging
import logging.handlers

def get_time() -> str:
    current_time = datetime.now()
    format_time = current_time.strftime("%Y-%m-%d:%H:%M:%S:%f")[:-4]
    return format_time

def geq(t1: tuple, t2: tuple) -> bool:
    """Compare two tuples. Return True only if every values in t1 is greater or equal than t2

    Args:
        t1
        t2
    """

    for idx in range(len(t1)):
        if t1[idx] < t2[idx]:
            return False
    return True

def gt(t1: tuple, t2: tuple) -> bool:
    """Compare two tuples. Return True only if every values in t1 is greater than t2

    Args:
        t1
        t2
    """

    for idx in range(len(t1)):
        if t1[idx] < t2[idx]:
            return False
    if t1 == t2:
        return False
    return True

class Msg_level(Enum):
    PRINT = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4

class Propius_logger:
    def __init__(self, log_file:str=None, verbose:bool=True, use_logging:bool=True):
        self.verbose = verbose
        self.use_logging = logging
        if self.use_logging:
            if not log_file:
                raise ValueError("Empty log file")
        
            handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            self.logger = logging.getLogger("mylogger")
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def print(self, message: str, level: int=Msg_level.PRINT):
        if self.verbose:
            print(f"{get_time()} {message}")
        if self.use_logging:
            if level == Msg_level.DEBUG:
                self.logger.debug(message)
            elif level == Msg_level.INFO:
                self.logger.info(message)
            elif level == Msg_level.WARNING:
                self.logger.warning(message)
            elif level == Msg_level.ERROR:
                self.logger.error(message)

class Group_condition:
    def __init__(self):
        # a list of condition
        self.condition_list = []
    def insert_condition(self, condition: list):
        # a condition is a tuple of two tuples. 
        # First tuple is the lower bound, the second is the upper bound
        # Logic relation between subcondition is AND
        # Logic relation between condition is OR  
        self.condition_list.append(condition)
    def check_condition(self, spec: tuple)->bool:
        for condition in self.condition_list:
            if geq(spec, condition[0]) and gt(condition[1], spec):
                return True
        return False


class Job_group:
    def __init__(self):
        self.cst_job_group_map = {}
        self.cst_group_condition_map = {}

    def update(self, cst: tuple, job_list: list, condition_list: Group_condition):
        self.cst_job_group_map[cst] = job_list
        self.cst_group_condition_map[cst] = condition_list

    def remove(self, cst: tuple):
        del self.cst_job_group_map[cst]
        del self.cst_group_condition_map[cst]

    def get_job_list(self, spec: tuple)->list:
        for cst, group_condition in self.cst_group_condition_map.items():
            if group_condition.check_condition(spec):
                return self.cst_job_group_map[cst]
        return []




    
