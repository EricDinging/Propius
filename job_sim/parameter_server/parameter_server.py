import pickle
import logging
import asyncio
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import yaml
import grpc
from propius_job.propius_job import *

_cleanup_coroutines = []


class Job(propius_pb2_grpc.JobServicer):
    def __init__(self, jm_ip, jm_port, ip, port, config):
        self.id = -1
        self.demand = int(config['demand'])
        self.public_constraint = tuple(config['public_constraint'])
        self.private_constraint = tuple(config['private_constraint'])
        self.est_total_round = int(config['total_round'])
        self.workload = int(config['workload'])
        # self.type = config['job_type']
        self.ip = ip
        self.port = port

        self.jm_channel = None
        self.jm_stub = None

        print(f"Job {self.id}: Init")
        self._connect_jm(jm_ip, jm_port)

        self.lock = asyncio.Lock()
        self.cv = asyncio.Condition(self.lock)
        self.cur_round = 1
        self.cur_result_list = []
        self.agg_result_list = []
        self.round_client_num = 0

        self.execution_start = False

    def _connect_jm(self, jm_ip: str, jm_port: int) -> None:
        self.jm_channel = grpc.insecure_channel(f'{jm_ip}:{jm_port}')
        self.jm_stub = propius_pb2_grpc.Job_managerStub(self.jm_channel)
        print(f"Job {self.id}: connecting to job manager at {jm_ip}:{jm_port}")

    def register(self) -> bool:
        job_info_msg = propius_pb2.job_info(
            est_demand=self.demand,
            est_total_round=self.est_total_round,
            public_constraint=pickle.dumps(self.public_constraint),
            private_constraint=pickle.dumps(self.private_constraint),
            ip=pickle.dumps(self.ip),
            port=self.port,
        )
        ack_msg = self.jm_stub.JOB_REGIST(job_info_msg)
        self.id = ack_msg.id
        ack = ack_msg.ack
        if not ack:
            print(f"Job {self.id}: register failed")
            return False
        else:
            print(f"Job {self.id}: register success")
            return True

    def request(self) -> bool:
        request_msg = propius_pb2.job_round_info(
            id=self.id,
            demand=self.demand,
        )
        self.execution_start = False
        ack_msg = self.jm_stub.JOB_REQUEST(request_msg)
        if not ack_msg.ack:
            print(
                f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} request failed")
            return False
        else:
            print(
                f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} request success")
            return True

    def end_request(self) -> bool:
        """optional, terminating request"""
        request_msg = propius_pb2.job_id(id=self.id)
        ack_msg = self.jm_stub.JOB_END_REQUEST(request_msg)
        if not ack_msg.ack:
            print(
                f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} end request failed")
            return False
        else:
            print(
                f"Job {self.id}: round: {self.cur_round}/{self.est_total_round} end request")
            return True

    def complete_job(self):
        req_msg = propius_pb2.job_id(id=self.id)
        self.jm_stub.JOB_FINISH(req_msg)

    def _close_round(self):
        # locked
        self.agg_result_list.append(sum(self.cur_result_list))
        self.cur_result_list.clear()
        self.cur_round += 1
        self.cv.notify()

    async def CLIENT_REPORT(self, request, context):
        async with self.lock:
            if self.cur_round > self.est_total_round:
                return propius_pb2.empty()
            client_id, result = request.client_id, request.result
            self.cur_result_list.append(result)
            print(f"Job {self.id}: round: {self.cur_round}/{self.est_total_round}: client {client_id} reported, {len(self.cur_result_list)}/{self.demand}")

            if len(self.cur_result_list) == self.demand:
                self._close_round()
            return propius_pb2.empty()

    async def CLIENT_REQUEST(self, request, context):
        client_id = request.id
        async with self.lock:
            if self.round_client_num >= self.demand or self.cur_round > self.est_total_round:
                return propius_pb2.plan(ack=False, workload=-1)
            print(
                f"Job {self.id}: round: {self.cur_round}/{self.est_total_round}: client {client_id} request for plan")
            self.round_client_num += 1
            if self.round_client_num >= self.demand:
                if not self.execution_start:
                    self.end_request()
                    self.execution_start = True
        return propius_pb2.plan(ack=True, workload=self.workload)


async def run(gconfig):
    async def server_graceful_shutdown():
        try:
            job.complete_job()
            job.jm_channel.close()
        except BaseException:
            pass
        print("==Job ending==")
        logging.info("Starting graceful shutdown...")
        await server.stop(5)

    server = grpc.aio.server()
    jm_ip, jm_port = gconfig['job_manager_ip'], int(
        gconfig['job_manager_port'])

    setup_file = str(sys.argv[1])
    ip = str(sys.argv[2])
    port = int(sys.argv[3])

    with open(setup_file, 'r') as yamlfile:
        config = yaml.load(yamlfile, Loader=yaml.FullLoader)
        job = Job(jm_ip, jm_port, ip, port, config)
        propius_pb2_grpc.add_JobServicer_to_server(job, server)
        server.add_insecure_port(f'{ip}:{port}')
        await server.start()
        print(f"Job: job started, listening on {ip}:{port}")

        _cleanup_coroutines.append(server_graceful_shutdown())

        if not job.register():
            return

        round = 1
        while round <= job.est_total_round:
            if not job.request():
                return
            async with job.lock:
                while job.cur_round != round + 1:
                    try:
                        job.round_client_num = 0
                        await asyncio.wait_for(job.cv.wait(), timeout=1000)
                    except asyncio.TimeoutError:
                        print("Timeout reached, shutting down job server")
                        return
                round += 1
        print(
            f"Job {job.id}: All round finished, result: {job.agg_result_list[-1]}")

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    global_setup_file = './global_config.yml'

    if len(sys.argv) != 4:
        print("Usage: python propius/job_sim/job.py <config file> job_ip job_port")
        exit(1)

    with open(global_setup_file, 'r') as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            print("Job read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(gconfig))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(str(e))
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
