import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import grpc
from propius_job.propius_job import *
from channels import parameter_server_pb2
from channels import parameter_server_pb2_grpc
from evaluation.commons import *
from collections import deque
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc
import os
import csv

_cleanup_coroutines = []

class Parameter_server(parameter_server_pb2_grpc.Parameter_serverServicer):
    def __init__(self, config):
        self.total_round = config['total_round']
        self.demand = config['demand']
        
        self.lock = asyncio.Lock()
        self.cv = asyncio.Condition(self.lock)

        self.cur_round = 1
        self.client_event_dict = {}

        self.round_client_num = 0
        self.round_result_cnt = 0

        self.execution_start = False #indicating whether the scheduling phase has passed

        self.propius_stub = Propius_job(job_config=config, verbose=True)

        self.propius_stub.connect()

        self.executor_ip = config['executor_ip']
        self.executor_port = config['executor_port']
        self.executor_channel = None
        self.executor_stub = None
        self._connect_to_executor()
        self.config = config

        result_dict = "./evaluation/ps_result"
        if not os.path.exists(result_dict):
            os.mkdir(result_dict)
        
        self.round_time_stamp = {}
        self.model_size = 0

    def _connect_to_executor(self):
        self.executor_channel = grpc.aio.insecure_channel(f"{self.executor_ip}:{self.executor_port}")
        self.executor_stub = executor_pb2_grpc.ExecutorStub(self.executor_channel)
        print(f"PS: connecting to executor on {self.executor_ip}: {self.executor_port}")

    def _close_round(self):
        # locked
        self.cur_round += 1
        self.cv.notify()

    def _init_event_queue(self, client_id:int):
        # locked
        #TODO other task
        event_q = deque()
        event_q.append({
            "event": UPDATE_MODEL,
            "meta": {
                "download_size": self.model_size
            },
            "data": {}
        })
        event_q.append({
            "event": CLIENT_TRAIN,
            "meta": {
                "batch_size": self.config["batch_size"],
                "local_steps": self.config["local_steps"]
            },
            "data": {}
        })
        event_q.append({
            "event": UPLOAD_MODEL,
            "meta": {
                "upload_size": self.model_size,
            },
            "data": {}
        })
        event_q.append({
            "event": SHUT_DOWN,
            "meta": {},
            "data": {}
        })
        self.client_event_dict[client_id] = event_q
    
    async def CLIENT_PING(self, request, context):
        client_id = request.id
        server_response_msg = parameter_server_pb2.server_response(
            event=SHUT_DOWN,
            meta=pickle.dumps(DUMMY_RESPONSE),
            data=pickle.dumps(DUMMY_RESPONSE)
            )
        async with self.lock:
            if client_id not in self.client_event_dict:
                if self.round_client_num < self.demand and self.cur_round <= self.total_round:
                    #TODO job train task register to executor
                    self._init_event_queue(client_id)
                    event_dict = self.client_event_dict[client_id].popleft()
                    print(event_dict)

                    server_response_msg = parameter_server_pb2.server_response(
                        event=event_dict["event"],
                        meta=pickle.dumps(event_dict["meta"]),
                        data=pickle.dumps(event_dict["data"])
                    )

                    self.round_client_num += 1

                    print(f"PS {self.propius_stub.id}-{self.cur_round}: client {client_id} ping, issue {event_dict['event']} event, {self.round_client_num}/{self.demand}")

                    #TODO send training task to executor
                    task_meta = {
                        "local_steps": self.config["local_steps"],
                        "learning_rate": self.config["learning_rate"],
                        "batch_size": self.config["batch_size"],
                        "num_loaders": self.config["num_loaders"],
                        "loss_decay": self.config["loss_decay"]
                    }
                    job_task_info_msg = executor_pb2.job_task_info(
                        job_id=self.propius_stub.id,
                        client_id=client_id,
                        round=self.cur_round,
                        event=CLIENT_TRAIN,
                        task_meta=pickle.dumps(task_meta)
                    )
                    await self.executor_stub.JOB_REGISTER_TASK(job_task_info_msg)

                    if self.round_client_num >= self.demand:
                        #TODO job aggregation task register to executor
                        if not self.execution_start:
                            #TODO send agg task to executor
                            task_meta = {}

                            job_task_info_msg = executor_pb2.job_task_info(
                                job_id=self.propius_stub.id,
                                client_id=-1,
                                round=self.cur_round,
                                event=AGGREGATE,
                                task_meta=pickle.dumps(task_meta)
                            )

                            await self.executor_stub.JOB_REGISTER_TASK(job_task_info_msg)
                            self.round_time_stamp[self.cur_round] = time.time()

                            self.propius_stub.round_end_request()
                            self.execution_start = True
            else:
                del self.client_event_dict[client_id]
            
            return server_response_msg

    
    async def CLIENT_EXECUTE_COMPLETION(self, request, context):
        client_id = request.id
        compl_event, status = request.event, request.status
        meta, data = request.meta, request.data

        #TODO result handling
        server_response_msg = parameter_server_pb2.server_response(
            event=SHUT_DOWN,
            meta=pickle.dumps(DUMMY_RESPONSE),
            data=pickle.dumps(DUMMY_RESPONSE)
            )

        async with self.lock:
            if compl_event == UPLOAD_MODEL:
                self.round_result_cnt += 1
                
            if client_id not in self.client_event_dict:
                return server_response_msg
            else:
                if len(self.client_event_dict[client_id]) == 0:
                    del self.client_event_dict[client_id]
                else:
                    next_event_dict = self.client_event_dict[client_id].popleft()
                    if len(self.client_event_dict[client_id]) == 0:
                        del self.client_event_dict[client_id]
                   
                    server_response_msg = parameter_server_pb2.server_response(
                        event=next_event_dict["event"],
                        meta=pickle.dumps(next_event_dict["meta"]),
                        data=pickle.dumps(next_event_dict["data"])
                    )

                    print(f"PS {self.propius_stub.id}-{self.cur_round}: client compl, issue {next_event_dict['event']} event")


                #TODO handling compl event
                if self.round_result_cnt >= self.demand:
                    self._close_round()
                return server_response_msg
            
    def gen_report(self):
        csv_file_name = f"./evaluation/ps_result/{self.propius_stub.id}.csv"
        fieldnames = ["round", "round_finish_time"]
        with open(csv_file_name, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(fieldnames)
            start_time = self.round_time_stamp[0]
            for round, time in self.round_time_stamp.items():
                writer.writerow([round, time-start_time])

async def run(config):
    async def server_graceful_shutdown():
        ps.gen_report()
        ps.propius_stub.complete_job()
        ps.propius_stub.close()
        
        task_meta = {}
        job_task_info_msg = executor_pb2.job_task_info(
            job_id=ps.propius_stub.id,
            client_id=-1,
            round=-1,
            event=JOB_FINISH,
            task_meta=pickle.dumps(task_meta)
        )
        await ps.executor_stub.JOB_REGISTER_TASK(job_task_info_msg)
        await ps.executor_channel.close()
        print("==Parameter server ending==")
        await server.stop(5)
    
    server = grpc.aio.server()
    ps = Parameter_server(config)
    _cleanup_coroutines.append(server_graceful_shutdown())

    # Register
    if not ps.propius_stub.register():
        print(f"Parameter server: register failed")
        return
    
    #TODO Register to executor
    job_meta = {
        "model": config["model"],
        "dataset": config["dataset"]
    }
    job_info_msg = executor_pb2.job_info(job_id=ps.propius_stub.id, 
                                         job_meta=pickle.dumps(job_meta))
    executor_ack = await ps.executor_stub.JOB_REGISTER(job_info_msg)
    ps.model_size = executor_ack.model_size
    ps.round_time_stamp[0] = time.time()

    parameter_server_pb2_grpc.add_Parameter_serverServicer_to_server(ps, server)
    server.add_insecure_port(f"{config['ip']}:{config['port']}")
    await server.start()
    print(f"Parameter server: parameter server started, listening on {config['ip']}:{config['port']}")

    round = 1
    async with ps.lock:
        while round <= ps.total_round:
            ps.execution_start = False
            ps.round_client_num = 0
            ps.round_result_cnt = 0
            if not ps.propius_stub.round_start_request(new_demand=False):
                print(f"Parameter server: round start request failed")
                return
            while ps.cur_round != round + 1:
                try:
                    # reset client event queue dict
                    ps.client_event_dict = {}
                    await asyncio.wait_for(ps.cv.wait(), timeout=1000)
                except asyncio.TimeoutError:
                    print("Timeout reached, shutting down job server")
                    return
            round += 1

    print(
        f"Parameter server: All round finished")
    
if __name__ == '__main__':
    
    if len(sys.argv) != 4:
        print("Usage: python test_job/parameter_server/parameter_server.py <config> <ip> <port>")
        exit(1)
        
    config_file = sys.argv[1]
    ip = sys.argv[2]
    port = int(sys.argv[3])

    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            print("Parameter server read config successfully")
            config["ip"] = ip
            config["port"] = port

            eval_config_file = './evaluation/evaluation_config.yml'
            with open(eval_config_file, 'r') as eval_config:
            
                eval_config = yaml.load(eval_config, Loader=yaml.FullLoader)
                config['executor_ip'] = eval_config['executor_ip']
                config['executor_port'] = eval_config['executor_port']
                loop = asyncio.get_event_loop()
                loop.run_until_complete(run(config))
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
