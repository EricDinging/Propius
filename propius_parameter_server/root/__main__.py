"""Root parameter server."""

from propius_parameter_server.channels import parameter_server_pb2, parameter_server_pb2_grpc
from propius_parameter_server.config import PROPIUS_PARAMETER_SERVER_ROOT, GLOBAL_CONFIG_FILE
from propius_parameter_server.root.parameter_server import Parameter_server
import yaml
import grpc
import asyncio

_cleanup_coroutines = []

async def serve(gconfig):
    async def server_graceful_shutdown():
        await server.stop(5)

    server = grpc.aio.server()
    root_ps = Parameter_server()
    parameter_server_pb2_grpc.add_Root_parameter_serverServicer_to_server(root_ps, server)
    server.add_insecure_port(f"{gconfig['root_ps_ip']}:{gconfig['root_ps_port']}")
    _cleanup_coroutines.append(server_graceful_shutdown())

    await server.start()
    print("root parameter server started")
    
    await server.wait_for_termination()

def main():
    with open(GLOBAL_CONFIG_FILE, "r") as gyamlfile:
        try:
            gconfig = yaml.load(gyamlfile, Loader=yaml.FullLoader)
            #TODO logging

            loop = asyncio.get_event_loop()
            loop.run_until_complete(serve(gconfig))

        except KeyboardInterrupt:
            pass

        except Exception as e:
            #TODO logging
            print(e)
        finally:
            loop.run_until_complete(*_cleanup_coroutines)

if __name__ == "__main__":
    main()