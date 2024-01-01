# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import propius_parameter_server.channels.parameter_server_pb2 as parameter__server__pb2


class Parameter_serverStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GET = channel.unary_unary(
            "/propius_parameter_server.Parameter_server/GET",
            request_serializer=parameter__server__pb2.job.SerializeToString,
            response_deserializer=parameter__server__pb2.job.FromString,
        )
        self.PUT = channel.unary_unary(
            "/propius_parameter_server.Parameter_server/PUT",
            request_serializer=parameter__server__pb2.job.SerializeToString,
            response_deserializer=parameter__server__pb2.ack.FromString,
        )
        self.PUSH = channel.unary_unary(
            "/propius_parameter_server.Parameter_server/PUSH",
            request_serializer=parameter__server__pb2.job.SerializeToString,
            response_deserializer=parameter__server__pb2.ack.FromString,
        )


class Parameter_serverServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GET(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def PUT(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def PUSH(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_Parameter_serverServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "GET": grpc.unary_unary_rpc_method_handler(
            servicer.GET,
            request_deserializer=parameter__server__pb2.job.FromString,
            response_serializer=parameter__server__pb2.job.SerializeToString,
        ),
        "PUT": grpc.unary_unary_rpc_method_handler(
            servicer.PUT,
            request_deserializer=parameter__server__pb2.job.FromString,
            response_serializer=parameter__server__pb2.ack.SerializeToString,
        ),
        "PUSH": grpc.unary_unary_rpc_method_handler(
            servicer.PUSH,
            request_deserializer=parameter__server__pb2.job.FromString,
            response_serializer=parameter__server__pb2.ack.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "propius_parameter_server.Parameter_server", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class Parameter_server(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GET(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/propius_parameter_server.Parameter_server/GET",
            parameter__server__pb2.job.SerializeToString,
            parameter__server__pb2.job.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def PUT(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/propius_parameter_server.Parameter_server/PUT",
            parameter__server__pb2.job.SerializeToString,
            parameter__server__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def PUSH(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/propius_parameter_server.Parameter_server/PUSH",
            parameter__server__pb2.job.SerializeToString,
            parameter__server__pb2.ack.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
