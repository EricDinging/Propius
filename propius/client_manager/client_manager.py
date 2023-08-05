import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import logging
import grpc
import yaml
import pickle
from propius.channels import propius_pb2
from propius.channels import propius_pb2_grpc
from db_stub import *
from cm_analyzer import *

_cleanup_coroutines = []

class Client_manager(propius_pb2_grpc.Client_managerServicer):
    def __init__(self, gconfig, cm_id:int):
        self.cm_id = cm_id
        self.ip = gconfig['client_manager'][self.cm_id]['ip']
        self.port = gconfig['client_manager'][self.cm_id]['port']
        self.sched_alg = gconfig['sched_alg']
        self.client_db_stub = Client_db_stub(gconfig, self.cm_id)
        self.job_db_stub = Job_db_stub(gconfig)
        self.cm_analyzer = CM_analyzer(self.sched_alg, gconfig['total_running_second'])
        self.max_client_num = gconfig['client_manager_id_weight']
        print(f"Client manager {self.cm_id} started, running {self.sched_alg}")

        self.lock = asyncio.Lock()
        self.client_num = 0

    async def CLIENT_CHECKIN(self, request, context):
        async with self.lock:
            client_id = self.max_client_num * self.cm_id + \
                self.client_num % self.max_client_num
            self.client_num += 1

        public_specification = pickle.loads(request.public_specification)

        self.client_db_stub.insert(client_id, public_specification)

        task_offer_list, task_private_constraint, job_size = self.job_db_stub.client_assign(public_specification)

        await self.cm_analyzer.client_checkin()

        
        if task_offer_list:
            print(f"Client manager {self.cm_id}: client {client_id} check in, offer: {task_offer_list}")
        
        return propius_pb2.cm_offer(
            client_id=client_id,
            task_offer=pickle.dumps(task_offer_list),
            private_constraint=pickle.dumps(task_private_constraint),
            total_job_num=job_size)
    
    async def CLIENT_PING(self, request, context):
        public_specification = self.client_db_stub.get(request.id)

        task_offer_list, task_private_constraint, job_size = self.job_db_stub.client_assign(public_specification)

        await self.cm_analyzer.client_ping()

        if task_offer_list:
            print(f"Client manager {self.cm_id}: client {request.id} ping, offer: {task_offer_list}")
        
        return propius_pb2.cm_offer(
            client_id=-1,
            task_offer=pickle.dumps(task_offer_list),
            private_constraint=pickle.dumps(task_private_constraint),
            total_job_num=job_size
        )
    
    async def CLIENT_ACCEPT(self, request, context):
        client_id, task_id = request.client_id, request.task_id
        result = self.job_db_stub.incr_amount(task_id)

        await self.cm_analyzer.client_accept(result)

        if not result:
            print(f"Client manager {self.cm_id}: job {task_id} over-assign")
            return propius_pb2.cm_ack(ack=False, job_ip=pickle.dumps(""), job_port=-1)
        print(f"Client manager {self.cm_id}: ack client {client_id}, job addr {result}")
        return propius_pb2.cm_ack(ack=True, job_ip=pickle.dumps(result[0]), 
                                  job_port=result[1])
    
async def serve(gconfig, cm_id:int):
    async def server_graceful_shutdown():
        client_manager.cm_analyzer.report(client_manager.cm_id)
        client_manager.client_db_stub.flushdb()
        print("Starting graceful shutdown...")
        await server.stop(5)
    
    server = grpc.aio.server()
    client_manager = Client_manager(gconfig, cm_id)
    propius_pb2_grpc.add_Client_managerServicer_to_server(client_manager, server)
    server.add_insecure_port(f'{client_manager.ip}:{client_manager.port}')
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.start()
    print(f"Client manager {client_manager.cm_id}: server started, listening on {client_manager.ip}:{client_manager.port}")
    await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    global_setup_file = './global_config.yml'

    if len(sys.argv) != 2:
        print("Usage: python propius/client_manager/client_manager.py <cm_id>")
        exit(1)

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            cm_id = int(sys.argv[1])
            print(f"Client manager {cm_id} read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig, cm_id))
        except KeyboardInterrupt:
            pass   
        except Exception as e:
            logger.error(str(e))
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()