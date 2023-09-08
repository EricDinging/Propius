import sys
[sys.path.append(i) for i in ['.', '..', '...']]
from propius.util.commons import *
from propius.client_manager.cm_monitor import *
from propius.client_manager.cm_db_portal import *
from propius.channels import propius_pb2_grpc
from propius.channels import propius_pb2
import pickle
import yaml
import grpc
import asyncio

_cleanup_coroutines = []


class Client_manager(propius_pb2_grpc.Client_managerServicer):
    def __init__(self, gconfig, cm_id: int, logger: My_logger):
        """Initialize client db portal

        Args:
            gconfig: config dictionary
                client_manager: list of client manager address
                    ip
                    port
                    client_db_port
                client_expire_time: expiration time of clients in the db
                client_manager_id_weight
                job_public_constraint: name of public constraint
                job_db_ip
                job_db_port
                sched_alg
                job_public_constraint: name of public constraint
                job_private_constraint: name of private constraint

            cm_id: id of the client manager is the user is client manager
            logger
        """

        self.cm_id = cm_id
        self.ip = gconfig['client_manager'][self.cm_id]['ip'] if not gconfig['use_docker'] else '0.0.0.0'
        self.port = gconfig['client_manager'][self.cm_id]['port']
        self.sched_alg = gconfig['sched_alg']
        self.client_db_portal = CM_client_db_portal(gconfig, self.cm_id, logger)
        self.job_db_portal = CM_job_db_portal(gconfig, logger)
        self.cm_monitor = CM_monitor(self.sched_alg, logger, gconfig['plot'])
        self.max_client_num = gconfig['client_manager_id_weight']
        self.lock = asyncio.Lock()
        self.client_num = 0
        self.logger = logger

    async def CLIENT_CHECKIN(self, request, context):
        """Hanle client check in, store client meatadata to database, and 
        return task offer list

        Args:
            public_specification: a tuple of client public specs

        Returns:
            cm_offer:
                client_id: assigned by client manager
                task_offer_list
                private_constraint
                total_job_num
        """

        async with self.lock:
            client_id = self.max_client_num * self.cm_id + \
                self.client_num % self.max_client_num
            self.client_num += 1

        public_specification = pickle.loads(request.public_specification)

        self.client_db_portal.insert(client_id, public_specification)

        task_offer_list, task_private_constraint, job_size = self.job_db_portal.client_assign(
            public_specification, self.sched_alg)
        
        await self.cm_monitor.client_checkin()

        if len(task_offer_list) > 0:
            self.logger.print(
                f"Client manager {self.cm_id}: client {client_id} check in, offer: {task_offer_list}", INFO)

        return propius_pb2.cm_offer(
            client_id=client_id,
            task_offer=pickle.dumps(task_offer_list),
            private_constraint=pickle.dumps(task_private_constraint),
            total_job_num=job_size)

    async def CLIENT_PING(self, request, context):
        """Hanle client check in, fetch client meatadata from database, and 
        return task offer list. This method should be called if previous client 
        task selection failed.

        Args:
            id

        Returns:
            cm_offer:
                client_id: assigned by client manager
                task_offer_list
                private_constraint
                total_job_num
        """

        public_specification = self.client_db_portal.get(request.id)

        task_offer_list, task_private_constraint, job_size = self.job_db_portal.client_assign(
            public_specification, self.sched_alg)

        await self.cm_monitor.client_ping()

        if len(task_offer_list) > 0:
            self.logger.print(
                f"Client manager {self.cm_id}: client {request.id} ping, offer: {task_offer_list}", INFO)

        return propius_pb2.cm_offer(
            client_id=-1,
            task_offer=pickle.dumps(task_offer_list),
            private_constraint=pickle.dumps(task_private_constraint),
            total_job_num=job_size
        )

    async def CLIENT_ACCEPT(self, request, context):
        """Handle client acceptance of a task, increment allocation amount of the corresponding job, if current amount is smaller than the corresponding round demand. Return job parameter server address, and ack. 
        Otherwise, job allocation amount will not increased by the calling client, 
        and the client fails to be assigned to this task.

        Args:
            client_id
            task_id

        Returns:
            cm_ack:
                ack
                job_ip
                job_port 
        """

        client_id, task_id = request.client_id, request.task_id
        result = self.job_db_portal.incr_amount(task_id)

        await self.cm_monitor.client_accept(result != None)

        if not result:
            self.logger.print(
                f"Client manager {self.cm_id}: job {task_id} over-assign", WARNING)
            return propius_pb2.cm_ack(
                ack=False, job_ip=pickle.dumps(""), job_port=-1)
        self.logger.print(
            f"Client manager {self.cm_id}: ack client {client_id}, job addr {result}", INFO)
        return propius_pb2.cm_ack(ack=True, job_ip=pickle.dumps(result[0]),
                                  job_port=result[1])
    
    async def HEART_BEAT(self, request, context):
        return propius_pb2.ack(ack=True)

async def serve(gconfig, cm_id: int, logger: My_logger):
    async def server_graceful_shutdown():
        logger.print(f"=====Client manager shutting down=====", WARNING)
        client_manager.cm_monitor.report(client_manager.cm_id)
        client_manager.client_db_portal.flushdb()
        await server.stop(5)

    server = grpc.aio.server()
    client_manager = Client_manager(gconfig, cm_id, logger)
    propius_pb2_grpc.add_Client_managerServicer_to_server(
        client_manager, server)
    server.add_insecure_port(f'{client_manager.ip}:{client_manager.port}')
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.start()
    logger.print(f"Client manager {client_manager.cm_id}: server started, listening on {client_manager.ip}:{client_manager.port}",
                 INFO)
    await server.wait_for_termination()

if __name__ == '__main__':
    global_setup_file = './propius/global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            if len(sys.argv) != 2:
                raise ValueError("Usage: python propius/client_manager/client_manager.py <cm_id>")

            cm_id = int(sys.argv[1])
            log_file = f'./propius/monitor/log/cm_{cm_id}.log'
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            logger = My_logger(log_file=log_file, verbose=gconfig['verbose'], use_logging=True)
            logger.print(f"Client manager {cm_id} read config successfully", INFO)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig, cm_id, logger))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e, ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
