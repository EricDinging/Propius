"""Distributor of client traffics to client managers."""

from propius.util import Msg_level, Propius_logger
from propius.load_balancer.load_balancer import Load_balancer
from propius.channels import propius_pb2_grpc
import yaml
import grpc
import asyncio
import os

_cleanup_coroutines = []

async def serve(gconfig, logger):
    async def server_graceful_shutdown():
        logger.print(f"=====Load balancer shutting down=====", Msg_level.WARNING)
        load_balancer.lb_monitor.report()

        heartbeat_task.cancel()
        await heartbeat_task

        await load_balancer._disconnect_cm()
        await server.stop(5)

    server = grpc.aio.server()
    load_balancer = Load_balancer(gconfig, logger)
    propius_pb2_grpc.add_Load_balancerServicer_to_server(load_balancer, server)
    server.add_insecure_port(f'{load_balancer.ip}:{load_balancer.port}')
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.start()
    logger.print(f"Load balancer: server started, listening on {load_balancer.ip}:{load_balancer.port}", Msg_level.INFO)

    heartbeat_task = asyncio.create_task(load_balancer.heartbeat_routine())

    await server.wait_for_termination()

if __name__ == '__main__':
    log_file = './propius/monitor/log/lb.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    global_setup_file = './propius/global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            logger = Propius_logger(log_file=log_file, verbose=gconfig["verbose"], use_logging=True)
            logger.print(f"Load balancer read config successfully", Msg_level.INFO)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig, logger))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.print(e, Msg_level.ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()
