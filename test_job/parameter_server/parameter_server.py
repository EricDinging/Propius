import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import pickle
import logging
import asyncio
import yaml
import grpc
from propius_job.propius_job import * # communication with Propius
from channels import parameter_server_pb2
from channels import parameter_server_pb2_grpc

_cleanup_coroutines = []


class Parameter_server(parameter_server_pb2_grpc.Parameter_serverServicer):
    def __init__(self, config):
        self.est_total_round = config['total_round']
        self.demand = config['demand']
        self.workload = config['workload']

        self.lock = asyncio.Lock()
        self.cv = asyncio.Condition(self.lock)
        self.cur_round = 1
        self.cur_result_list = []
        self.agg_result_list = []
        self.round_client_num = 0

        self.execution_start = False

        #TODO config init
        self.propius_stub = Propius_job(job_config=config, verbose=True)
        
        self.propius_stub.connect()

    def _close_round(self):
        # locked
        self.agg_result_list.append(sum(self.cur_result_list))
        self.cur_result_list.clear()
        self.cur_round += 1
        self.cv.notify()

    async def CLIENT_REPORT(self, request, context):
        async with self.lock:
            if self.cur_round > self.est_total_round:
                return parameter_server_pb2.empty()
            client_id, result = request.client_id, request.result
            self.cur_result_list.append(result)
            print(f"Parameter server: round: {self.cur_round}/{self.est_total_round}: client {client_id} reported, {len(self.cur_result_list)}/{self.demand}")

            if len(self.cur_result_list) == self.demand:
                self._close_round()
            return parameter_server_pb2.empty()

    async def CLIENT_REQUEST(self, request, context):
        client_id = request.id
        async with self.lock:
            if self.round_client_num >= self.demand or self.cur_round > self.est_total_round:
                return parameter_server_pb2.plan(ack=False, workload=-1)
            print(
                f"Parameter server: round: {self.cur_round}/{self.est_total_round}: client {client_id} request for plan")
            self.round_client_num += 1
            if self.round_client_num >= self.demand:
                if not self.execution_start:
                    self.propius_stub.round_end_request()
                    self.execution_start = True
        return parameter_server_pb2.plan(ack=True, workload=self.workload)


async def run(config):
    async def server_graceful_shutdown():
        ps.propius_stub.close()
        print("==Parameter server ending==")
        #TODO logging.info("Starting graceful shutdown...")
        await server.stop(5)

    server = grpc.aio.server()
    ps = Parameter_server(config)
    _cleanup_coroutines.append(server_graceful_shutdown())

    # Register
    if not ps.propius_stub.register():
        print(f"Parameter server: register failed")
        return
    
    parameter_server_pb2_grpc.add_Parameter_serverServicer_to_server(ps, server)
    server.add_insecure_port(f"{config['ip']}:{config['port']}")
    await server.start()
    print(f"Parameter server: parameter server started, listening on {config['ip']}:{config['port']}")

    round = 1
    while round <= ps.est_total_round:
        #TODO error handling
        ps.execution_start = False
        if not ps.propius_stub.round_start_request(new_demand=False):
            print(f"Parameter server: round start request failed")
            return
        async with ps.lock:
            while ps.cur_round != round + 1:
                try:
                    ps.round_client_num = 0
                    await asyncio.wait_for(ps.cv.wait(), timeout=1000)
                except asyncio.TimeoutError:
                    print("Timeout reached, shutting down job server")
                    return
            round += 1
    #TODO error handling
    ps.propius_stub.complete_job()
    print(
        f"Parameter server: All round finished, result: {ps.agg_result_list[-1]}")

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    config_file = './test_job/parameter_server/test_profile.yml'

    with open(config_file, 'r') as config:
        try:
            config = yaml.load(config, Loader=yaml.FullLoader)
            print("Parameter server read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error(str(e))
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
