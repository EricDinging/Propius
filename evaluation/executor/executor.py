import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import grpc
import pickle
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc
from evaluation.executor.task_pool import *
from evaluation.commons import *

_cleanup_coroutines = []

class Executor(executor_pb2_grpc.ExecutorServicer):
    def __init__(self, config):
        self.ip = config['executor_ip']
        self.port = config['executor_port']
        self.task_pool = Task_pool()

    async def JOB_REGISTER(self, request, context):
        job_id = request.job_id
        job_meta = pickle.loads(request.job_meta)
        job_data = {
            "model_weights": {}
        } #TODO get model weights
        await self.task_pool.init_job(job_id, job_meta, job_data)
        return executor_pb2.ack(ack=True)
    
    async def JOB_REGISTER_TASK(self, request, context):
        job_id, client_id = request.job_id, request.client_id
        round, event = request.round, request.event
        task_meta = pickle.loads(request.task_meta)

        await self.task_pool.insert_job_task(job_id=job_id, 
                                             client_id=client_id,
                                             round=round,
                                             event=event,
                                             task_meta=task_meta)
        return executor_pb2.ack(ack=True)
    
    async def execute(self):
        #TODO
        while True:
            execute_meta = self.task_pool.get_next_task()
            if not execute_meta:
                await asyncio.sleep(5)
                continue

            if execute_meta['event'] == JOB_FINISH:
                await self.task_pool.remove_job(execute_meta['job_id'])
            
            elif execute_meta['event'] == CLIENT_TRAIN:
                #TODO train
                await asyncio.sleep(5)

            elif execute_meta['event'] == AGGREGATE:
                #TODO aggregate
                await asyncio.sleep(1)


    
async def run(config):
    async def server_graceful_shutdown():
        print("==Executor ending==")
        #TODO handling result
        executor.task_pool.gen_report()
        await server.stop(5)

    server = grpc.aio.server()
    executor = Executor(config)
    _cleanup_coroutines.append(server_graceful_shutdown())

    executor_pb2_grpc.add_ExecutorServicer_to_server(executor, server)
    server.add_insecure_port(f"{executor.ip}:{executor.port}")
    await server.start()
    print(f"Executor: executor started, listening on {executor.ip}:{executor.port}")

    await executor.execute()

if __name__ == '__main__':
    config_file = './evaluation/evaluation_config.yml'
    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            print("Executor read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()