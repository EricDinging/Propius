import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import yaml
import grpc
from propius_job.propius_job import *
from channels import parameter_server_pb2
from channels import parameter_server_pb2_grpc
from commons import *
from collections import deque

_cleanup_coroutines = []

class Parameter_server(parameter_server_pb2_grpc.Parameter_serverServicer):
    def __init__(self, config):
        self.total_round = config['total_round']
        self.demand = config['demand']
        
        self.lock = asyncio.Lock()
        self.cv = asyncio.Condition(self.lock)

        self.cur_round = 1
        self.client_event_dict = {}

        self.execution_start = False #indicating whether the scheduling phase has passed

        self.propius_stub = Propius_job(job_config=config, verbose=True)

        self.propius_stub.connect()

    def _close_round(self):
        # locked
        self.cur_round += 1
        self.cv.notify()

    def _init_event_queue(self, client_id:int):
        # locked
        #TODO other task
        event_q = deque()
        event_q.append(UPDATE_MODEL)
        event_q.append(CLIENT_TRAIN)
        event_q.append(UPLOAD_MODEL)
        event_q.append(SHUT_DOWN)
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
                if len(self.client_event_dict) >= self.demand or self.cur_round > self.total_round:
                    return server_response_msg
                else:
                    #TODO job train task register to executor
                    self._init_event_queue(client_id)
                    server_response_msg = parameter_server_pb2.server_response(
                        event=self.client_event_dict[client_id].popleft(),
                        meta=pickle.dumps(DUMMY_RESPONSE),
                        data=pickle.dumps(DUMMY_RESPONSE)
                    )
                    if len(self.client_event_dict) == self.demand:
                        #TODO job aggregation task register to executor
                        if not self.execution_start:
                            self.propius_stub.round_end_request()
                            self.execution_start = True
            else:
                return server_response_msg
        
        return super().CLIENT_PING(request, context)
    
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
            if client_id not in self.client_event_dict:
                return server_response_msg
            else:
                if len(self.client_event_dict[client_id]) == 0:
                    del self.client_event_dict[client_id]
                else:
                    next_event = self.client_event_dict[client_id].popleft()
                    if len(self.client_event_dict[client_id]) == 0:
                        del self.client_event_dict[client_id]
                    server_response_msg = parameter_server_pb2.server_response(
                        event=next_event,
                        meta=pickle.dumps(DUMMY_RESPONSE),
                        data=pickle.dumps(DUMMY_RESPONSE)
                    )
                #TODO handling compl event
                if len(self.client_event_dict) == 0:
                    self._close_round()
                return server_response_msg

async def run(config):
    async def server_graceful_shutdown():
        ps.propius_stub.close()
        print("==Parameter server ending==")
        await server.stop(5)
    
    server = grpc.aio.server()
    ps = Parameter_server(config)
    _cleanup_coroutines.append(server_graceful_shutdown())

    # Register
    if not ps.propius_stub.register():
        print(f"Parameter server: register failed")
        return
    
    #TODO Register to worker

    parameter_server_pb2_grpc.add_Parameter_serverServicer_to_server(ps, server)
    server.add_insecure_port(f"{config['ip']}:{config['port']}")
    await server.start()
    print(f"Parameter server: parameter server started, listening on {config['ip']}:{config['port']}")

    round = 1
    while round <= ps.total_round:
        ps.execution_start = False
        if not ps.propius_stub.round_start_request(new_demand=False):
            print(f"Parameter server: round start request failed")
            return
        async with ps.lock:
            while ps.cur_round != round + 1:
                try:
                    # reset client event queue dict
                    ps.client_event_dict = {}
                except asyncio.TimeoutError:
                    print("Timeout reached, shutting down job server")
                    return
            round += 1
    ps.propius_stub.complete_job()
    print(
        f"Parameter server: All round finished, result: {ps.agg_result_list[-1]}")
    
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
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run(config))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
