# Define Basic FL Events
UPDATE_MODEL = 'update_model'
MODEL_TEST = 'model_test'
SHUT_DOWN = 'shut_down'
# START_ROUND = 'start_round'
# CLIENT_CONNECT = 'client_connect'
CLIENT_TRAIN = 'client_train'
DUMMY_EVENT = 'dummy_event'
UPLOAD_MODEL = 'upload_model'
AGGREGATE = 'aggregate'
JOB_FINISH = 'finish'

# PLACEHOLD
DUMMY_RESPONSE = 'N'

# TENSORFLOW = 'tensorflow'
# PYTORCH = 'pytorch'

JOB_META = {
    "model": "",
    "dataset": "",
}

TASK_META = {
    "client_id": -1,
    "round": -1,
    "event": "",
    "local_steps": 0,
    "learning_rate": 0,
    "batch_size": 0,
    "test_ratio": 0,
    "test_bsz": 0, 
    "num_loaders": 5,
    "loss_decay": 0.9
}

EXECUTE_META = JOB_META.update(TASK_META)

result_dict = {
    "accuracy": 0,
    "loss": 0,
    #training==
    "moving_loss": 0,
    "trained_size": 0,
}

out_put_class = {'Mnist': 10, 'cifar10': 10, "imagenet": 1000, 'emnist': 47, 'amazon': 5,
               'openImg': 596, 'google_speech': 35, 'femnist': 62, 'yelp': 5, 'inaturalist': 1010
               }

MAX_MESSAGE_LENGTH = 1 * 1024 * 1024 * 1024  # 1GB


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
    if verbose:
        print(f"{get_time()} {message}")
    if level == DEBUG:
        logging.debug(message)
    elif level == INFO:
        logging.info(message)
    elif level == WARNING:
        logging.warning(message)
    elif level == ERROR:
        logging.error(message)


global_config_file = "./evaluation/evaluation_config.yml"

with open(global_config_file, "r") as gyamlfile:
    gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
    verbose = gconfig["verbose"]


