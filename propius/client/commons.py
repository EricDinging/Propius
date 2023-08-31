from datetime import datetime

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

def get_time() -> str:
    current_time = datetime.now()
    format_time = current_time.strftime("%Y-%m-%d:%H:%M:%S:%f")[:-4]
    return format_time


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