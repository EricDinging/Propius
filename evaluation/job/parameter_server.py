import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import grpc
from propius.job.propius_job import *
from channels import parameter_server_pb2
from channels import parameter_server_pb2_grpc
from evaluation.commons import *
from collections import deque
from evaluation.executor.channels import executor_pb2
from evaluation.executor.channels import executor_pb2_grpc
import os
import csv
import logging
import logging.handlers

_cleanup_coroutines = []

class Parameter_server(parameter_server_pb2_grpc.Parameter_serverServicer):
    def __init__(self, config):
        self.total_round = config['total_round']
        self.demand = config['demand']
        self.over_demand = self.demand if "over_selection" not in config else \
            int(config["over_selection"] * config["demand"])

        if config["use_docker"]:
            config["executor_ip"] = "executor"

        job_config = {
            "public_constraint": config["public_constraint"],
            "private_constraint": config["private_constraint"],
            "total_round": config["total_round"],
            "demand": config["demand"] if "over_selection" not in config else \
                    int(config["over_selection"] * config["demand"]),
            "job_manager_ip": config["job_manager_ip"] if not config["use_docker"] else "job_manager",
            "job_manager_port": config["job_manager_port"],
            "ip": config["ip"] if not config["use_docker"] else "jobs",
            "port": config["port"]
        }

        self.ip = config["ip"] if not config["use_docker"] else "0.0.0.0"
        self.port = config["port"]

        self.lock = asyncio.Lock()
        self.cv = asyncio.Condition(self.lock)

        self.cur_round = 1
        self.client_event_dict = {}

        self.round_client_num = 0
        self.round_result_cnt = 0

        self.execution_start = False #indicating whether the scheduling phase has passed

        self.propius_stub = Propius_job(job_config=job_config, verbose=True, logging=True)

        # self.propius_stub.connect()

        self.executor_ip = config['executor_ip']
        self.executor_port = config['executor_port']
        self.executor_channel = None
        self.executor_stub = None
        self._connect_to_executor()
        self.config = config
        self.round_time_stamp = {}
        self.round_sched_time = {}
        self.model_size = 0

    def _connect_to_executor(self):
        self.executor_channel = grpc.aio.insecure_channel(f"{self.executor_ip}:{self.executor_port}")
        self.executor_stub = executor_pb2_grpc.ExecutorStub(self.executor_channel)
        custom_print(f"PS: connecting to executor on {self.executor_ip}:{self.executor_port}", INFO)

    async def _close_round(self):
        # locked
        task_meta = {}
        job_task_info_msg = executor_pb2.job_task_info(
            job_id=self.propius_stub.id,
            client_id=-1,
            round=self.cur_round,
            event=AGGREGATE,
            task_meta=pickle.dumps(task_meta),
            task_data=pickle.dumps(DUMMY_RESPONSE)
        )
        await self.executor_stub.JOB_REGISTER_TASK(job_task_info_msg)

        self.round_time_stamp[self.cur_round] = time.time()
        self.cur_round += 1

    def _init_event_queue(self, client_id:int):
        # locked
        #TODO other task
        event_q = deque()
        event_q.append({
            "event": UPDATE_MODEL,
            "meta": {
                "download_size": self.model_size,
                "round": self.cur_round
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

    async def heartbeat_routine(self):
        try:
            while True:
                await asyncio.sleep(30)
                try:
                    self.sched_portal.HEART_BEAT(propius_pb2.empty())
                except:
                    pass
        except asyncio.CancelledError:
            pass
    
    async def CLIENT_PING(self, request, context):
        client_id = request.id
        server_response_msg = parameter_server_pb2.server_response(
            event=SHUT_DOWN,
            meta=pickle.dumps(DUMMY_RESPONSE),
            data=pickle.dumps(DUMMY_RESPONSE)
            )
        async with self.lock:
            if self.execution_start:
                if client_id in self.client_event_dict:
                    event_dict = self.client_event_dict[client_id].popleft()
                    server_response_msg = parameter_server_pb2.server_response(
                        event=event_dict["event"],
                        meta=pickle.dumps(event_dict["meta"]),
                        data=pickle.dumps(event_dict["data"])
                    )
                    custom_print(f"PS {self.propius_stub.id}-{self.cur_round}: client {client_id} ping, "
                        f"issue {event_dict['event']} event", INFO)
                    
            else:
                custom_print(f"PS {self.propius_stub.id}-{self.cur_round}: client {client_id} ping, "
                            f"issue dummy event, {self.round_client_num}/{self.demand}", INFO)
                
                if client_id not in self.client_event_dict:
                    if self.round_client_num < self.over_demand and self.cur_round <= self.total_round:
                        #TODO job train task register to executor
                        self._init_event_queue(client_id)

                        server_response_msg = parameter_server_pb2.server_response(
                            event=DUMMY_EVENT,
                            meta=pickle.dumps(DUMMY_RESPONSE),
                            data=pickle.dumps(DUMMY_RESPONSE)
                        )

                        self.round_client_num += 1

                        if self.round_client_num >= self.over_demand:
                            if not self.execution_start:
                                custom_print(f"PS {self.propius_stub.id}-{self.cur_round}: start execution", INFO)
                                self.propius_stub.end_request()
                                self.execution_start = True
                                self.round_sched_time[self.cur_round] = time.time() - self.round_sched_time[self.cur_round]
                else:
                    server_response_msg = parameter_server_pb2.server_response(
                        event=DUMMY_EVENT,
                        meta=pickle.dumps(DUMMY_RESPONSE),
                        data=pickle.dumps(DUMMY_RESPONSE)
                    )
            return server_response_msg

    
    async def CLIENT_EXECUTE_COMPLETION(self, request, context):
        client_id = request.id
        compl_event, status = request.event, request.status
        meta, data = pickle.loads(request.meta), pickle.loads(request.data)

        #TODO result handling
        server_response_msg = parameter_server_pb2.server_response(
            event=SHUT_DOWN,
            meta=pickle.dumps(DUMMY_RESPONSE),
            data=pickle.dumps(DUMMY_RESPONSE)
            )

        async with self.lock:
            if meta["round"] != self.cur_round:
                return server_response_msg
            if client_id not in self.client_event_dict:
                return server_response_msg
            if self.round_result_cnt > self.demand:
                return server_response_msg
            
            if compl_event == UPLOAD_MODEL:
                custom_print(f"PS {self.propius_stub.id}-{self.cur_round}: client {client_id} complete, "
                             f"issue SHUT_DOWN event, {self.round_result_cnt}/{self.demand}", INFO)
                self.round_result_cnt += 1
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
                    task_meta=pickle.dumps(task_meta),
                    task_data=pickle.dumps(DUMMY_RESPONSE)
                )
                await self.executor_stub.JOB_REGISTER_TASK(job_task_info_msg)
                
            # Get next event
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

                custom_print(f"PS {self.propius_stub.id}-{self.cur_round}: client compl, issue {next_event_dict['event']} event", INFO)

            if self.round_result_cnt >= self.demand:
                await self._close_round()
                self.cv.notify()
            return server_response_msg
            
    def gen_report(self):
        csv_file_name = f"./evaluation/monitor/job/job_{self.port}_{self.config['sched_alg']}_{self.propius_stub.id}.csv"
        fieldnames = ["round", "round_finish_time", "round_sched_time"]
        with open(csv_file_name, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(fieldnames)
            start_time = self.round_time_stamp[0]
            for round, time in self.round_time_stamp.items():
                writer.writerow([round, time-start_time, self.round_sched_time[round]])

async def run(config):
    async def server_graceful_shutdown():
        ps.gen_report()
        ps.propius_stub.complete_job()

        heartbeat_task.cancel()
        await heartbeat_task
        
        #ps.propius_stub.close()
        
        task_meta = {}
        job_task_info_msg = executor_pb2.job_task_info(
            job_id=ps.propius_stub.id,
            client_id=-1,
            round=ps.cur_round if ps.cur_round <= ps.total_round else ps.total_round,
            event=JOB_FINISH,
            task_meta=pickle.dumps(task_meta),
            task_data=pickle.dumps(DUMMY_RESPONSE)
        )
        await ps.executor_stub.JOB_REGISTER_TASK(job_task_info_msg)
        await ps.executor_channel.close()
        custom_print("==Parameter server ending==", WARNING)
        await server.stop(5)
    
    server = grpc.aio.server()
    ps = Parameter_server(config)
    _cleanup_coroutines.append(server_graceful_shutdown())

    # Register
    if not ps.propius_stub.register():
        custom_print(f"Parameter server: register failed", ERROR)
        return
    
    grad_policy = config["gradient_policy"]
    job_meta = {
        "model": config["model"],
        "dataset": config["dataset"],
        "gradient_policy": grad_policy
    }
    if grad_policy == "fed-yogi":
        job_meta["yogi_eta"] = config["yogi_eta"]
        job_meta["yogi_tau"] = config["yogi_tau"]
        job_meta["yogi_beta1"] = config["yogi_beta1"]
        job_meta["yogi_beta2"] = config["yogi_beta2"]

    job_info_msg = executor_pb2.job_info(job_id=ps.propius_stub.id, 
                                         job_meta=pickle.dumps(job_meta))
    executor_ack = await ps.executor_stub.JOB_REGISTER(job_info_msg)
    ps.model_size = executor_ack.model_size
    ps.round_time_stamp[0] = time.time()

    parameter_server_pb2_grpc.add_Parameter_serverServicer_to_server(ps, server)
    server.add_insecure_port(f"{ps.ip}:{ps.port}")
    await server.start()
    custom_print(f"Parameter server: parameter server started, listening on {ps.ip}:{ps.port}", INFO)

    ps.round_sched_time[0] = 0
    round = 1

    heartbeat_task = asyncio.create_task(ps.heartbeat_routine())

    async with ps.lock:
        while round <= ps.total_round:
            ps.execution_start = False
            ps.round_client_num = 0
            ps.round_result_cnt = 0
            ps.round_sched_time[ps.cur_round] = time.time()
            if not ps.propius_stub.start_request(new_demand=False):
                custom_print(f"Parameter server: round start request failed", WARNING)
                return
            while ps.cur_round != round + 1:
                try:
                    # reset client event queue dict
                    ps.client_event_dict = {}
                    await asyncio.wait_for(ps.cv.wait(), timeout=config["connection_timeout"])
                except asyncio.TimeoutError:
                    await ps._close_round()
                    break

            round += 1

    custom_print(
        f"Parameter server: All round finished", INFO)
    
if __name__ == '__main__':
    
    if len(sys.argv) != 4:
        custom_print("Usage: python test_job/parameter_server/parameter_server.py <config> <ip> <port>", ERROR)
        exit(1)
        
    config_file = sys.argv[1]
    ip = sys.argv[2]
    port = int(sys.argv[3])

    log_file = f'./evaluation/monitor/job/job_{port}.log'

    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            custom_print("Parameter server read config successfully", INFO)
            config["ip"] = ip
            config["port"] = port

            eval_config_file = './evaluation/evaluation_config.yml'
            with open(eval_config_file, 'r') as eval_config:
            
                eval_config = yaml.load(eval_config, Loader=yaml.FullLoader)
                config['executor_ip'] = eval_config['executor_ip']
                config['executor_port'] = eval_config['executor_port']
                config['job_manager_ip'] = eval_config['job_manager_ip']
                config['job_manager_port'] = eval_config['job_manager_port']
                config['use_docker'] = eval_config['use_docker']
                config['sched_alg'] = eval_config['sched_alg']
                loop = asyncio.get_event_loop()
                loop.run_until_complete(run(config))
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            custom_print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
