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
import logging
import logging.handlers

_cleanup_coroutines = []

class Executor(executor_pb2_grpc.ExecutorServicer):
    def __init__(self, config: dict, logger: My_logger):
        self.ip = config['executor_ip'] if not config['use_docker'] else '0.0.0.0'
        self.port = config['executor_port']
        self.task_pool = Task_pool(config)
        self.worker = Worker_manager(config, logger)
        self.sched_alg = config['sched_alg']
        self.config = config
        self.round_timeout = config['round_timeout']

        self.lock = asyncio.Lock()
        self.logger = logger
        self.job_train_task_dict = {}
        self.job_test_task_dict = {}

        result_dict = f"./evaluation/executor/result_{self.sched_alg}"
        if not os.path.exists(result_dict):
            os.mkdir(result_dict)

    async def JOB_REGISTER(self, request, context):
        job_id = request.job_id
        job_meta = pickle.loads(request.job_meta)

        model_size = await self.worker.init_job(job_id=job_id, 
                                   dataset_name=job_meta["dataset"],
                                   model_name=job_meta["model"],
                                   args=job_meta
                                   )
        self.logger.print(f"Executor: job {job_id} registered", INFO)
        await self.task_pool.init_job(job_id, job_meta)
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

    async def wait_for_testing_task(self, job_id:int, round: int):
        async with self.lock:
            if job_id not in self.job_test_task_dict:
                return
            task_list = self.job_test_task_dict[job_id]
            del self.job_test_task_dict[job_id]

        try:
            completed, pending = await asyncio.wait(task_list,
                                                    timeout=self.round_timeout,
                                                    return_when=asyncio.ALL_COMPLETED)
        except Exception as e:
            self.logger.print(e, ERROR)
        
        aggregate_test_result = {
            "test_loss": 0,
            "acc": 0,
            "acc_5": 0,
            "test_len": 0
        }

        for task in completed:
            try:
                results = await task
                for key in aggregate_test_result.keys():
                    aggregate_test_result[key] += results[key]
                
            except Exception as e:
                self.logger.print(e, ERROR)
        
        for key in aggregate_test_result.keys():
            if key != "test_len":
                aggregate_test_result[key] /= aggregate_test_result["test_len"]
            
        aggregate_test_result = {
            MODEL_TEST: aggregate_test_result
        }
        
        await self.task_pool.report_result(job_id=job_id,
                                            round=round,
                                            result=aggregate_test_result)
    
    async def wait_for_training_task(self, job_id:int, round: int):
        async with self.lock:
            if job_id not in self.job_train_task_dict:
                return
            task_list = self.job_train_task_dict[job_id]
            del self.job_train_task_dict[job_id]

        try:
            completed, pending = await asyncio.wait(task_list,
                                                timeout=self.round_timeout,
                                                return_when=asyncio.ALL_COMPLETED)
        except Exception as e:
            self.logger.print(e, ERROR)
        
        for task in completed:
            try:
                results = await task
                await self.task_pool.report_result(job_id=job_id,
                                                    round=round,
                                                    result=results)
            except Exception as e:
                self.logger.print(e, ERROR)

    async def execute(self):
        while True:
            execute_meta = await self.task_pool.get_next_task()
            
            if not execute_meta:
                await asyncio.sleep(5)
                continue
            
            job_id = execute_meta['job_id']
            client_id = execute_meta['client_id']
            event = execute_meta['event']

            del execute_meta['job_id']
            del execute_meta['client_id']
            del execute_meta['event']

            self.logger.print(f"Executor: execute job {job_id} {event}", INFO)

            if event == JOB_FINISH:
                await self.wait_for_training_task(job_id=job_id, round=execute_meta['round'])
                await self.wait_for_testing_task(job_id=job_id, round=execute_meta['round'])

                await self.task_pool.gen_report(job_id=job_id,
                                                sched_alg=self.config["sched_alg"])
                await self.task_pool.remove_job(job_id=job_id)
                await self.worker.remove_job(job_id=job_id)
                
                async with self.lock:
                    if job_id in self.job_train_task_dict:
                        del self.job_train_task_dict[job_id]
                    if job_id in self.job_test_task_dict:
                        del self.job_test_task_dict[job_id]

                continue
            
            elif event == CLIENT_TRAIN:
                # create asyncio task for training task
                await self.wait_for_testing_task(job_id=job_id, round=execute_meta['round']-1)

                task = asyncio.create_task(
                    self.worker.execute(event=CLIENT_TRAIN,
                                          job_id=job_id,
                                          client_id=client_id,
                                          args=execute_meta)
                )

                async with self.lock:
                    if job_id not in self.job_train_task_dict:
                        self.job_train_task_dict[job_id] = []
                    self.job_train_task_dict[job_id].append(task)

            elif event == MODEL_TEST:
                
                await self.wait_for_training_task(job_id=job_id, round=execute_meta['round'])

                async with self.lock:
                    if job_id not in self.job_test_task_dict:
                        self.job_test_task_dict[job_id] = []
                    for i in range(self.config["client_test_num"]):
                        task = asyncio.create_task(
                            self.worker.execute(event=MODEL_TEST,
                                                job_id=job_id,
                                                client_id=i,
                                                args=execute_meta)
                        )
                        self.job_test_task_dict[job_id].append(task)

            elif event == AGGREGATE:
                # wait for all pending training task to complete
                
                await self.wait_for_training_task(job_id=job_id, round=execute_meta['round'])

                results = await self.worker.execute(event=AGGREGATE,
                                                    job_id=job_id,
                                                    client_id=-1,
                                                    args=execute_meta)
                
                await self.task_pool.report_result(job_id=job_id,
                                                    round=execute_meta['round'],
                                                    result=results)

    
async def run(config, logger):
    async def server_graceful_shutdown():
        await executor.task_pool.gen_all_report(executor.sched_alg)
        logger.print("==Executor ending==", WARNING)
        heartbeat_task.cancel()
        await heartbeat_task
        await executor.worker._disconnect()
        await server.stop(5)

    server = grpc.aio.server()
    executor = Executor(config, logger)
    _cleanup_coroutines.append(server_graceful_shutdown())

    heartbeat_task = asyncio.create_task(executor.worker.heartbeat_routine())

    executor_pb2_grpc.add_ExecutorServicer_to_server(executor, server)
    server.add_insecure_port(f"{executor.ip}:{executor.port}")
    await server.start()
    logger.print(f"Executor: executor started, listening on {executor.ip}:{executor.port}", INFO)

    await executor.execute()

if __name__ == '__main__':
    log_file = './evaluation/executor/ex_app.log'
    logger = My_logger(log_file=log_file, verbose=True, use_logging=True)

    config_file = './evaluation/evaluation_config.yml'
    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            logger.print("Executor read config successfully")
            
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config, logger))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()