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

def encode_specs(**kargs) -> tuple[list, list]:
    """Encode client specs. Eg. encode_specs(CPU_F=18, RAM=8).

    Args:
        Keyword arguments

    Raises:
        ValueError: if input key is not recognized
    """

    public_spec_dict = {
        CPU_F: 0,
        RAM: 0,
        FP16_MEM: 0,
        ANDROID_OS: 0,
    }

    private_spec_dict = {
        DATASET_SIZE: 0
    }

    for key in public_spec_dict.keys():
        if key in kargs:
            public_spec_dict[key] = kargs[key]

    for key in private_spec_dict.keys():
        if key in kargs:
            private_spec_dict[key] = kargs[key]

    for key in kargs.keys():
        if key not in public_spec_dict and key not in private_spec_dict:
            raise ValueError(f"{key} spec is not supported")

    # TODO encoding, value check

    return (list(public_spec_dict.values()),
            list(private_spec_dict.values()))

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
        self.condition_list = ""
    def insert_condition(self, condition: str):
        self.condition_list + condition


class Job_group:
    def __init__(self):
        self.cst_job_group_map = {}
        self.cst_group_condition_map = {}

    def insert(self, cst: tuple, job_list: list):
        self.cst_job_group_map[cst] = job_list
        self.cst_group_condition_map[cst] = Group_condition()

    def update(self, cst: tuple, condition: str):
        if cst in self.cst_group_condition_map:
            self.cst_group_condition_map[cst].insert_condition(condition)

    def remove(self, cst: tuple):
        if cst in self.cst_job_group_map:
            del self.cst_job_group_map[cst]
            del self.cst_group_condition_map[cst]


    
