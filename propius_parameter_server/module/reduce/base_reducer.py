import torch
from propius_parameter_server.util.commons import Msg_level, Propius_logger
from functools import reduce

def base_reduce(a: list, b: list, func = torch.Tensor.add_):
    """Handler for reduction. Receives a, b, performs reduction on a and b, 
    and places the result in a.
    """
    
    for i, x in enumerate(b):
        a[i] = reduce(func, [a[i], x])
    return a


if __name__ == "__main__":
    base_reduce()