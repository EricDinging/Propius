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


    
