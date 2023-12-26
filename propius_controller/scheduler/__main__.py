"""Job scheduler."""

from propius_controller.util import Msg_level, Propius_logger
from propius_controller.channels import propius_pb2_grpc
from propius_controller.config import PROPIUS_CONTROLLER_ROOT, GLOBAL_CONFIG_FILE
import asyncio
import yaml
import grpc
import os

_cleanup_coroutines = []


async def serve(gconfig, logger):
    async def server_graceful_shutdown():
        logger.print("=====Scheduler shutting down=====", Msg_level.WARNING)
        scheduler.sc_monitor.report()

        try:
            plot_task.cancel()
            await plot_task
        except asyncio.exceptions.CancelledError:
            pass

        await server.stop(5)

    server = grpc.aio.server()

    if gconfig["sched_alg"] == "fifo":
        from propius_controller.scheduler.module.fifo_scheduler import FIFO_scheduler as Scheduler
    else:
        from propius_controller.scheduler.module.base_scheduler import Scheduler

    scheduler = Scheduler(gconfig, logger)
    propius_pb2_grpc.add_SchedulerServicer_to_server(scheduler, server)
    server.add_insecure_port(f"{scheduler.ip}:{scheduler.port}")
    await server.start()

    plot_task = asyncio.create_task(scheduler.plot_routine())

    logger.print(
        f"Scheduler: server started, listening on {scheduler.ip}:{scheduler.port}, running {gconfig['sched_alg']}",
        Msg_level.INFO,
    )
    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == "__main__":
    with open(GLOBAL_CONFIG_FILE, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            log_file_path = PROPIUS_CONTROLLER_ROOT / gconfig["scheduler_log_path"]
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            logger = Propius_logger(
                log_file=log_file_path, verbose=gconfig["verbose"], use_logging=True
            )
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
