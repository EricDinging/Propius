# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import evaluation.job.channels.parameter_server_pb2 as parameter__server__pb2


class Parameter_serverStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CLIENT_CHECKIN = channel.unary_unary(
                '/parameter_server.Parameter_server/CLIENT_CHECKIN',
                request_serializer=parameter__server__pb2.client_id.SerializeToString,
                response_deserializer=parameter__server__pb2.server_response.FromString,
                )
        self.CLIENT_PING = channel.unary_unary(
                '/parameter_server.Parameter_server/CLIENT_PING',
                request_serializer=parameter__server__pb2.client_id.SerializeToString,
                response_deserializer=parameter__server__pb2.server_response.FromString,
                )
        self.CLIENT_EXECUTE_COMPLETION = channel.unary_unary(
                '/parameter_server.Parameter_server/CLIENT_EXECUTE_COMPLETION',
                request_serializer=parameter__server__pb2.client_complete.SerializeToString,
                response_deserializer=parameter__server__pb2.server_response.FromString,
                )


class Parameter_serverServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CLIENT_CHECKIN(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CLIENT_PING(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CLIENT_EXECUTE_COMPLETION(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Parameter_serverServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CLIENT_CHECKIN': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_CHECKIN,
                    request_deserializer=parameter__server__pb2.client_id.FromString,
                    response_serializer=parameter__server__pb2.server_response.SerializeToString,
            ),
            'CLIENT_PING': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_PING,
                    request_deserializer=parameter__server__pb2.client_id.FromString,
                    response_serializer=parameter__server__pb2.server_response.SerializeToString,
            ),
            'CLIENT_EXECUTE_COMPLETION': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_EXECUTE_COMPLETION,
                    request_deserializer=parameter__server__pb2.client_complete.FromString,
                    response_serializer=parameter__server__pb2.server_response.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'parameter_server.Parameter_server', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Parameter_server(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CLIENT_CHECKIN(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/parameter_server.Parameter_server/CLIENT_CHECKIN',
            parameter__server__pb2.client_id.SerializeToString,
            parameter__server__pb2.server_response.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CLIENT_PING(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/parameter_server.Parameter_server/CLIENT_PING',
            parameter__server__pb2.client_id.SerializeToString,
            parameter__server__pb2.server_response.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CLIENT_EXECUTE_COMPLETION(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/parameter_server.Parameter_server/CLIENT_EXECUTE_COMPLETION',
            parameter__server__pb2.client_complete.SerializeToString,
            parameter__server__pb2.server_response.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
