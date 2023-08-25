import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import grpc
import pickle
from evaluation.single_executor.channels import executor_pb2
from evaluation.single_executor.channels import executor_pb2_grpc
from evaluation.single_executor.task_pool import *
from evaluation.single_executor.worker import *
from evaluation.commons import *
import os
import time

_cleanup_coroutines = []

class Executor(executor_pb2_grpc.ExecutorServicer):
    def __init__(self, config: dict, gconfig: dict):
        self.ip = config['executor_ip']
        self.port = config['executor_port']
        self.task_pool = Task_pool(config)
        self.worker = Worker(config)
        self.gconfig = gconfig

        result_dict = f"./evaluation/result_{self.gconfig['sched_alg']}"
        if not os.path.exists(result_dict):
            os.mkdir(result_dict)

    async def JOB_REGISTER(self, request, context):
        job_id = request.job_id
        job_meta = pickle.loads(request.job_meta)

        #TODO get model weights
        await self.task_pool.init_job(job_id, job_meta)
        model_size = await self.worker.init_job(job_id=job_id, 
                                   dataset_name=job_meta["dataset"],
                                   model_name=job_meta["model"],
                                   )

        return executor_pb2.register_ack(ack=True, model_size=model_size)
    
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
            execute_meta = await self.task_pool.get_next_task()
            
            if not execute_meta:
                await asyncio.sleep(5)
                continue
            
            job_id = execute_meta['job_id']

            custom_print(f"Executor: execute job {job_id} {execute_meta['event']}", INFO)

            if execute_meta['event'] == JOB_FINISH:
                await self.task_pool.gen_report(job_id=job_id,
                                                sched_alg=self.gconfig["sched_alg"])
                await self.task_pool.remove_job(job_id=job_id)
                await self.worker.remove_job(job_id=job_id)
                continue
            
            elif execute_meta['event'] == CLIENT_TRAIN:
                client_id = execute_meta['client_id']
                results = await self.worker.execute(event=CLIENT_TRAIN,
                                          job_id=job_id,
                                          client_id=client_id,
                                          args=execute_meta)
                
                results = {CLIENT_TRAIN+str(client_id): results}

            elif execute_meta['event'] == MODEL_TEST:
                results = await self.worker.execute(
                    event=MODEL_TEST,
                    job_id=job_id,
                    client_id=execute_meta['client_id'],
                    args=execute_meta
                )
                results = {
                    MODEL_TEST: results
                }

            elif execute_meta['event'] == AGGREGATE:
                results = await self.worker.execute(event=AGGREGATE,
                                                    job_id=job_id,
                                                    client_id=-1,
                                                    args=execute_meta)
                results = {AGGREGATE: results}
            await self.task_pool.report_result(job_id=job_id,
                                                round=execute_meta['round'],
                                                result=results)

    
async def run(config, gconfig):
    async def server_graceful_shutdown():
        await executor.task_pool.gen_all_report(executor.gconfig["sched_alg"])
        custom_print("==Executor ending==", INFO)
        #TODO handling result
        await server.stop(5)

    server = grpc.aio.server()
    executor = Executor(config, gconfig)
    _cleanup_coroutines.append(server_graceful_shutdown())

    executor_pb2_grpc.add_ExecutorServicer_to_server(executor, server)
    server.add_insecure_port(f"{executor.ip}:{executor.port}")
    await server.start()
    custom_print(f"Executor: executor started, listening on {executor.ip}:{executor.port}", INFO)

    await executor.execute()

if __name__ == '__main__':
    config_file = './evaluation/evaluation_config.yml'
    logging.basicConfig(level=logging.INFO,
                        filename='./evaluation/single_executor/app.log',
                        filemode='w', 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',)
    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            custom_print("Executor read config successfully")
            with open('./propius/global_config.yml', 'r') as gconfig:
                gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)
                
                loop = asyncio.get_event_loop()
                loop.run_until_complete(run(config, gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            custom_print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()