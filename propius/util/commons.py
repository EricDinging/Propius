from datetime import datetime
import yaml
import logging

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

def custom_print(message: str, level: int=PRINT):
    if level == PRINT:
        if verbose:
            print(f"{get_time()} {message}")
        # logging.info(message)
    elif level == DEBUG:
        logging.debug(message)
    elif level == INFO:
        logging.info(message)
    elif level == WARNING:
        logging.warning(message)
    else:
        logging.error(message)


global_config_file = "./propius/global_config.yml"

with open(global_config_file, "r") as gyamlfile:
    gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
    verbose = gconfig["verbose"]


    
