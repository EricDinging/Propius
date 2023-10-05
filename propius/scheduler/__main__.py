"""Job scheduler."""

from propius.util import Msg_level, Propius_logger
from propius.scheduler.scheduler import Scheduler
from propius.channels import propius_pb2_grpc
import asyncio
import yaml
import grpc
import os

_cleanup_coroutines = []

async def serve(gconfig, logger):
    async def server_graceful_shutdown():
        logger.print("=====Scheduler shutting down=====", Msg_level.WARNING)
        scheduler.sc_monitor.report()
        await server.stop(5)
    
    server = grpc.aio.server()
    scheduler = Scheduler(gconfig, logger)
    propius_pb2_grpc.add_SchedulerServicer_to_server(scheduler, server)
    server.add_insecure_port(f'{scheduler.ip}:{scheduler.port}')
    await server.start()
    
    logger.print(f"Scheduler: server started, listening on {scheduler.ip}:{scheduler.port}, running {scheduler.sched_alg}",
                 Msg_level.INFO)
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()

if __name__ == '__main__':
    log_file = './propius/monitor/log/sc.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    global_setup_file = './propius/global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            logger = Propius_logger(log_file=log_file, verbose=gconfig["verbose"], use_logging=True)
            logger.print(f"scheduler read config successfully")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig, logger))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.print(e, Msg_level.ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()