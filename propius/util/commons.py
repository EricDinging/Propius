from datetime import datetime
import yaml
import logging
import logging.handlers

def get_time() -> str:
    current_time = datetime.now()
    format_time = current_time.strftime("%Y-%m-%d:%H:%M:%S:%f")[:-4]
    return format_time

PRINT = 0
DEBUG = 1
INFO = 2
WARNING = 3
ERROR = 4

CPU_F = "cpu_f"
RAM = "ram"
FP16_MEM = "fp16_mem"
ANDROID_OS = "android_os"
DATASET_SIZE = "dataset_size"

def geq(t1: tuple, t2: tuple) -> bool:
    """Compare two tuples. Return True only if every values in t1 is greater than t2

    Args:
        t1
        t2
    """

    for idx in range(len(t1)):
        if t1[idx] < t2[idx]:
            return False
    return True

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

def encode_constraints(**kargs) -> tuple[list, list]:
    """Encode job constraints. Eg. encode_constraints(CPU_F=18, RAM=8).

    Args:
        Keyword arguments

    Raises:
        ValueError: if input key is not recognized
    """

    public_constraint_dict = {
        CPU_F: 0,
        RAM: 0,
        FP16_MEM: 0,
        ANDROID_OS: 0,
    }

    private_constraint_dict = {
        DATASET_SIZE: 0
    }

    for key in public_constraint_dict.keys():
        if key in kargs:
            public_constraint_dict[key] = kargs[key]

    for key in private_constraint_dict.keys():
        if key in kargs:
            private_constraint_dict[key] = kargs[key]

    for key in kargs.keys():
        if key not in public_constraint_dict and key not in private_constraint_dict:
            raise ValueError(f"{key} constraint is not supported")

    # TODO encoding, value check

    return (list(public_constraint_dict.values()),
            list(private_constraint_dict.values()))

verbose = True

class My_logger:
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

    def print(self, message: str, level: int=PRINT):
        if self.verbose:
            print(f"{get_time()} {message}")
        if self.use_logging:
            if level == DEBUG:
                self.logger.debug(message)
            elif level == INFO:
                self.logger.info(message)
            elif level == WARNING:
                self.logger.warning(message)
            elif level == ERROR:
                self.logger.error(message)


    
