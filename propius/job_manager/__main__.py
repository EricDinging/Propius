"""FL Job Manager."""

from propius.util import Msg_level, Propius_logger
from propius.job_manager.job_manager import Job_manager
from propius.channels import propius_pb2_grpc
import asyncio
import os
import yaml
import grpc

_cleanup_coroutines = []

async def serve(gconfig, logger):
    async def server_graceful_shutdown():
        logger.print(f"=====Job manager shutting down=====", Msg_level.WARNING)
        job_manager.jm_monitor.report()
        job_manager.job_db_portal.flushdb()

        heartbeat_task.cancel()
        plot_task.cancel()
        await heartbeat_task

        try:
            await job_manager.sched_channel.close()
        except Exception as e:
            logger.print(e, Msg_level.WARNING)
        await server.stop(5)

    server = grpc.aio.server()
    job_manager = Job_manager(gconfig, logger)
    propius_pb2_grpc.add_Job_managerServicer_to_server(job_manager, server)
    server.add_insecure_port(f'{job_manager.ip}:{job_manager.port}')
    await server.start()

    heartbeat_task = asyncio.create_task(job_manager.heartbeat_routine())
    plot_task = asyncio.create_task(job_manager.plot_routine())

    logger.print(f"Job manager: server started, listening on {job_manager.ip}:{job_manager.port}", Msg_level.INFO)
    _cleanup_coroutines.append(server_graceful_shutdown())

    # signal.signal(signal.SIGTERM, sigterm_handler)

    await server.wait_for_termination()

if __name__ == '__main__':
    log_file = './propius/monitor/log/jm.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    global_setup_file = './propius/global_config.yml'

    with open(global_setup_file, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            logger = Propius_logger(log_file=log_file, verbose=gconfig["verbose"], use_logging=True)
            logger.print(f"Job manager read config successfully", Msg_level.INFO)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig, logger))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.print(e, Msg_level.ERROR)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)
            loop.close()