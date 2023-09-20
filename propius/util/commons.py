from datetime import datetime
from enum import Enum
import logging
import logging.handlers

def get_time() -> str:
    current_time = datetime.now()
    format_time = current_time.strftime("%Y-%m-%d:%H:%M:%S:%f")[:-4]
    return format_time

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



    
