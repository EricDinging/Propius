import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import grpc
import pickle
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc
from evaluation.executor.task_pool import *
from evaluation.executor.worker_manager import *
from evaluation.commons import *
import os

_cleanup_coroutines = []

class Executor(executor_pb2_grpc.ExecutorServicer):
    def __init__(self, config: dict, gconfig: dict):
        self.ip = config['executor_ip']
        self.port = config['executor_port']
        self.task_pool = Task_pool(config)
        self.worker = Worker_manager(config)
        self.gconfig = gconfig

        self.job_task_dict = {}

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
    
    async def wait_for_training_task(self, job_id:int, round: int):
        if job_id not in self.job_task_dict:
            return
        completed, pending = await asyncio.wait(self.job_task_dict[job_id], 
                                                return_when=asyncio.ALL_COMPLETED)
        
        for task in completed:
            try:
                results = await task
                await self.task_pool.report_result(job_id=job_id,
                                                    round=round,
                                                    result=results)
            except:
                pass

    
    async def execute(self):
        #TODO
        while True:
            execute_meta = await self.task_pool.get_next_task()
            
            if not execute_meta:
                await asyncio.sleep(5)
                continue
            
            job_id = execute_meta['job_id']

            print(f"Executor: execute job {job_id} {execute_meta['event']}")

            if execute_meta['event'] == JOB_FINISH:
                await self.task_pool.gen_report(job_id=job_id,
                                                sched_alg=self.gconfig["sched_alg"])
                await self.task_pool.remove_job(job_id=job_id)
                await self.worker.remove_job(job_id=job_id)
                
                try:
                    del self.job_task_dict[job_id]
                except:
                    pass

                continue
            
            elif execute_meta['event'] == CLIENT_TRAIN:
                # create asyncio task for training task
                if job_id not in self.job_task_dict:
                    self.job_task_dict[job_id] = []
                    
                client_id = execute_meta['client_id']
                task = asyncio.create_task(
                    self.worker.execute(event=CLIENT_TRAIN,
                                          job_id=job_id,
                                          client_id=client_id,
                                          args=execute_meta)
                )

                self.job_task_dict[job_id].append(task)

            elif execute_meta['event'] == MODEL_TEST:

                await self.wait_for_training_task(job_id=job_id, round=execute_meta['round'])

                results = await self.worker.execute(
                    event=MODEL_TEST,
                    job_id=job_id,
                    client_id=execute_meta['client_id'],
                    args=execute_meta
                )

                await self.task_pool.report_result(job_id=job_id,
                                                    round=execute_meta['round'],
                                                    result=results)

            elif execute_meta['event'] == AGGREGATE:
                # wait for all pending training task to complete
                
                await self.wait_for_training_task(job_id=job_id, round=execute_meta['round'])

                results = await self.worker.execute(event=AGGREGATE,
                                                    job_id=job_id,
                                                    client_id=-1,
                                                    args=execute_meta)
                
                await self.task_pool.report_result(job_id=job_id,
                                                    round=execute_meta['round'],
                                                    result=results)

    
async def run(config, gconfig):
    async def server_graceful_shutdown():
        await executor.task_pool.gen_all_report(executor.gconfig["sched_alg"])
        print("==Executor ending==")
        heartbeat_task.cancel()
        await heartbeat_task
        await executor.worker._disconnect()
        await server.stop(5)

    server = grpc.aio.server()
    executor = Executor(config, gconfig)
    _cleanup_coroutines.append(server_graceful_shutdown())

    heartbeat_task = asyncio.create_task(executor.worker.heartbeat_routine())

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
            with open('./propius/global_config.yml', 'r') as gconfig:
                gconfig = yaml.load(gconfig, Loader=yaml.FullLoader)
                
                loop = asyncio.get_event_loop()
                loop.run_until_complete(run(config, gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()