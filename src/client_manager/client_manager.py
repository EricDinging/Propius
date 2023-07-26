import sys
[sys.path.append(i) for i in ['.', '..', '...']]
import asyncio
import logging
import grpc
import yaml
from src.channels import propius_pb2
from src.channels import propius_pb2_grpc
from db_stub import *
from cm_analyzer import *

_cleanup_coroutines = []

class Client_manager(propius_pb2_grpc.Client_managerServicer):
    def __init__(self, gconfig):
        self.ip = gconfig['client_manager_ip']
        self.port = int(gconfig['client_manager_port'])
        self.sched_alg = gconfig['sched_alg']
        self.client_db_stub = Client_db_stub(gconfig)
        self.job_db_stub = Job_db_stub(gconfig)
        self.cm_analyzer = CM_analyzer(self.sched_alg, gconfig['total_running_second'])
        print(f"Client manager started, running {self.sched_alg}")

    async def CLIENT_CHECKIN(self, request, context):
        client_id, metric_msg = request.client_id, request.cmetrics
        metrics = (metric_msg.cpu, metric_msg.memory, metric_msg.os)

        self.client_db_stub.insert(client_id, metrics)

        task_offer_list, job_size = self.job_db_stub.client_assign(metrics)

        await self.cm_analyzer.client_checkin(task_offer_list, job_size)

        if not task_offer_list:
            return propius_pb2.cm_offer(task_offer="NA")
        task_offer = ' '.join(str(x) for x in task_offer_list)
        print(f"Client manager: client {client_id} check in, offer: {task_offer}")
        return propius_pb2.cm_offer(task_offer=task_offer)
    
    async def CLIENT_ACCEPT(self, request, context):
        client_id, task_id = request.client_id, request.task_id
        result = self.job_db_stub.incr_amount(task_id)

        await self.cm_analyzer.client_accept(result)

        if not result:
            print(f"Client manager: job {task_id} over-assign")
            return propius_pb2.cm_ack(ack=False, job_ip="", job_port=-1)
        print(f"Client manager: ack client {client_id}, job addr {result}")
        return propius_pb2.cm_ack(ack=True, job_ip=result[0], job_port=result[1])
    
async def serve(gconfig):
    async def server_graceful_shutdown():
        client_manager.cm_analyzer.report()
        client_manager.client_db_stub.flushdb()
        print("Starting graceful shutdown...")
        await server.stop(5)
    
    server = grpc.aio.server()
    client_manager = Client_manager(gconfig)
    propius_pb2_grpc.add_Client_managerServicer_to_server(client_manager, server)
    server.add_insecure_port(f'{client_manager.ip}:{client_manager.port}')
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.start()
    print(f"Client manager: server started, listening on {client_manager.ip}:{client_manager.port}")
    await server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    global_setup_file = './global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            print("Client manager read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig))
        except KeyboardInterrupt:
            pass   
        except Exception as e:
            logger.error(str(e))
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()