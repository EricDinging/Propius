"""FL Edge Device (Client) Manager"""

import sys
import os
from propius.util import Msg_level, Propius_logger
from propius.client_manager.client_manager import Client_manager
from propius.channels import propius_pb2_grpc
import yaml
import grpc
import asyncio

_cleanup_coroutines = []

async def serve(gconfig, cm_id: int, logger: Propius_logger):
    async def server_graceful_shutdown():
        logger.print(f"=====Client manager shutting down=====", Msg_level.WARNING)
        client_manager.cm_monitor.report(client_manager.cm_id)
        client_manager.client_db_portal.flushdb()
        client_manager.temp_client_db_portal.flushdb()
        await server.stop(5)

    server = grpc.aio.server()
    client_manager = Client_manager(gconfig, cm_id, logger)
    propius_pb2_grpc.add_Client_managerServicer_to_server(
        client_manager, server)
    server.add_insecure_port(f'{client_manager.ip}:{client_manager.port}')
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.start()
    logger.print(f"Client manager {client_manager.cm_id}: server started, listening on {client_manager.ip}:{client_manager.port}",
                 Msg_level.INFO)
    await server.wait_for_termination()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError("Usage: python propius/client_manager/client_manager.py <cm_id>")
    global_setup_file = './propius/global_config.yml'
    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            cm_id = int(sys.argv[1])
            log_file = f'./propius/monitor/log/cm_{cm_id}.log'
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            logger = Propius_logger(log_file=log_file, verbose=gconfig['verbose'], use_logging=True)
            logger.print(f"Client manager {cm_id} read config successfully", Msg_level.INFO)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig, cm_id, logger))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e, Msg_level.ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()



