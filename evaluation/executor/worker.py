import asyncio
import yaml
import grpc
import pickle
import sys
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc
from collections import deque

_cleanup_coroutines = []

class Worker(executor_pb2_grpc.WorkerServicer):
    def __init__(self, id: int, config: dict):
        self.id = id
        
        if id >= len(config["worker"]):
            raise ValueError("Invalid worker ID")
        
        self.ip = config["worker"][id]["ip"]
        self.port = config["worker"][id]["port"]
        device = config["worker"][id]["device"] if config["use_cuda"] else "cpu"

        self.lock = asyncio.Lock()
        self.task_to_do = deque()
        self.task_finished = {}

    async def INIT(self, request, context):
        return super().INIT(request, context)
    
    async def REMOVE(self, request, context):
        return super().REMOVE(request, context)
    
    async def TRAIN(self, request, context):
        return super().TRAIN(request, context)
    
    async def TEST(self, request, context):
        return super().TEST(request, context)
    
    async def PING(self, request, context):
        return super().PING(request, context)
    
    async def HEART_BEAT(self, request, context):
        async with self.lock:
            status_msg = executor_pb2.worker_status(task_size=len(self.task_to_do))
            return status_msg
        
    async def execute(self):
        while True:

            pass
    
async def run(config):
    async def server_graceful_shutdown():
        pass

    server = grpc.aio.server()

    if len(sys.argv) != 2:
        print("Usage: python evaluation/executor/worker.py <id>")

    id = sys.argv[1]
    worker = Worker(id, config)
    _cleanup_coroutines.append(server_graceful_shutdown())

    executor_pb2_grpc.add_WorkerServicer_to_server(worker, server)
    server.add_insecure_port(f"{worker.ip}:{worker.port}")
    await server.start()
    print(f"Worker {worker.id}: started, listening on {worker.ip}:{worker.port}")

    await worker.execute()

if __name__ == '__main__':
    config_file = './evaluation/evaluation_config.yml'
    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
