# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import propius.channels.propius_pb2 as propius__pb2


class JobStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CLIENT_REQUEST = channel.unary_unary(
                '/propius.Job/CLIENT_REQUEST',
                request_serializer=propius__pb2.client_id.SerializeToString,
                response_deserializer=propius__pb2.plan.FromString,
                )
        self.CLIENT_REPORT = channel.unary_unary(
                '/propius.Job/CLIENT_REPORT',
                request_serializer=propius__pb2.client_report.SerializeToString,
                response_deserializer=propius__pb2.empty.FromString,
                )


class JobServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CLIENT_REQUEST(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CLIENT_REPORT(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_JobServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CLIENT_REQUEST': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_REQUEST,
                    request_deserializer=propius__pb2.client_id.FromString,
                    response_serializer=propius__pb2.plan.SerializeToString,
            ),
            'CLIENT_REPORT': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_REPORT,
                    request_deserializer=propius__pb2.client_report.FromString,
                    response_serializer=propius__pb2.empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'propius.Job', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Job(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CLIENT_REQUEST(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Job/CLIENT_REQUEST',
            propius__pb2.client_id.SerializeToString,
            propius__pb2.plan.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CLIENT_REPORT(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Job/CLIENT_REPORT',
            propius__pb2.client_report.SerializeToString,
            propius__pb2.empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class Job_managerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.JOB_REGIST = channel.unary_unary(
                '/propius.Job_manager/JOB_REGIST',
                request_serializer=propius__pb2.job_info.SerializeToString,
                response_deserializer=propius__pb2.job_register_ack.FromString,
                )
        self.JOB_REQUEST = channel.unary_unary(
                '/propius.Job_manager/JOB_REQUEST',
                request_serializer=propius__pb2.job_round_info.SerializeToString,
                response_deserializer=propius__pb2.ack.FromString,
                )
        self.JOB_END_REQUEST = channel.unary_unary(
                '/propius.Job_manager/JOB_END_REQUEST',
                request_serializer=propius__pb2.job_id.SerializeToString,
                response_deserializer=propius__pb2.ack.FromString,
                )
        self.JOB_FINISH = channel.unary_unary(
                '/propius.Job_manager/JOB_FINISH',
                request_serializer=propius__pb2.job_id.SerializeToString,
                response_deserializer=propius__pb2.empty.FromString,
                )


class Job_managerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def JOB_REGIST(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def JOB_REQUEST(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def JOB_END_REQUEST(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def JOB_FINISH(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Job_managerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'JOB_REGIST': grpc.unary_unary_rpc_method_handler(
                    servicer.JOB_REGIST,
                    request_deserializer=propius__pb2.job_info.FromString,
                    response_serializer=propius__pb2.job_register_ack.SerializeToString,
            ),
            'JOB_REQUEST': grpc.unary_unary_rpc_method_handler(
                    servicer.JOB_REQUEST,
                    request_deserializer=propius__pb2.job_round_info.FromString,
                    response_serializer=propius__pb2.ack.SerializeToString,
            ),
            'JOB_END_REQUEST': grpc.unary_unary_rpc_method_handler(
                    servicer.JOB_END_REQUEST,
                    request_deserializer=propius__pb2.job_id.FromString,
                    response_serializer=propius__pb2.ack.SerializeToString,
            ),
            'JOB_FINISH': grpc.unary_unary_rpc_method_handler(
                    servicer.JOB_FINISH,
                    request_deserializer=propius__pb2.job_id.FromString,
                    response_serializer=propius__pb2.empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'propius.Job_manager', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Job_manager(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def JOB_REGIST(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Job_manager/JOB_REGIST',
            propius__pb2.job_info.SerializeToString,
            propius__pb2.job_register_ack.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def JOB_REQUEST(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Job_manager/JOB_REQUEST',
            propius__pb2.job_round_info.SerializeToString,
            propius__pb2.ack.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def JOB_END_REQUEST(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Job_manager/JOB_END_REQUEST',
            propius__pb2.job_id.SerializeToString,
            propius__pb2.ack.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def JOB_FINISH(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Job_manager/JOB_FINISH',
            propius__pb2.job_id.SerializeToString,
            propius__pb2.empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class SchedulerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.JOB_SCORE_UPDATE = channel.unary_unary(
                '/propius.Scheduler/JOB_SCORE_UPDATE',
                request_serializer=propius__pb2.job_id.SerializeToString,
                response_deserializer=propius__pb2.ack.FromString,
                )


class SchedulerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def JOB_SCORE_UPDATE(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_SchedulerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'JOB_SCORE_UPDATE': grpc.unary_unary_rpc_method_handler(
                    servicer.JOB_SCORE_UPDATE,
                    request_deserializer=propius__pb2.job_id.FromString,
                    response_serializer=propius__pb2.ack.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'propius.Scheduler', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Scheduler(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def JOB_SCORE_UPDATE(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Scheduler/JOB_SCORE_UPDATE',
            propius__pb2.job_id.SerializeToString,
            propius__pb2.ack.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class Client_managerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CLIENT_CHECKIN = channel.unary_unary(
                '/propius.Client_manager/CLIENT_CHECKIN',
                request_serializer=propius__pb2.client_checkin.SerializeToString,
                response_deserializer=propius__pb2.cm_offer.FromString,
                )
        self.CLIENT_PING = channel.unary_unary(
                '/propius.Client_manager/CLIENT_PING',
                request_serializer=propius__pb2.client_id.SerializeToString,
                response_deserializer=propius__pb2.cm_offer.FromString,
                )
        self.CLIENT_ACCEPT = channel.unary_unary(
                '/propius.Client_manager/CLIENT_ACCEPT',
                request_serializer=propius__pb2.client_accept.SerializeToString,
                response_deserializer=propius__pb2.cm_ack.FromString,
                )


class Client_managerServicer(object):
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

    def CLIENT_ACCEPT(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Client_managerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CLIENT_CHECKIN': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_CHECKIN,
                    request_deserializer=propius__pb2.client_checkin.FromString,
                    response_serializer=propius__pb2.cm_offer.SerializeToString,
            ),
            'CLIENT_PING': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_PING,
                    request_deserializer=propius__pb2.client_id.FromString,
                    response_serializer=propius__pb2.cm_offer.SerializeToString,
            ),
            'CLIENT_ACCEPT': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_ACCEPT,
                    request_deserializer=propius__pb2.client_accept.FromString,
                    response_serializer=propius__pb2.cm_ack.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'propius.Client_manager', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Client_manager(object):
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
        return grpc.experimental.unary_unary(request, target, '/propius.Client_manager/CLIENT_CHECKIN',
            propius__pb2.client_checkin.SerializeToString,
            propius__pb2.cm_offer.FromString,
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
        return grpc.experimental.unary_unary(request, target, '/propius.Client_manager/CLIENT_PING',
            propius__pb2.client_id.SerializeToString,
            propius__pb2.cm_offer.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CLIENT_ACCEPT(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Client_manager/CLIENT_ACCEPT',
            propius__pb2.client_accept.SerializeToString,
            propius__pb2.cm_ack.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class Load_balancerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CLIENT_CHECKIN = channel.unary_unary(
                '/propius.Load_balancer/CLIENT_CHECKIN',
                request_serializer=propius__pb2.client_checkin.SerializeToString,
                response_deserializer=propius__pb2.cm_offer.FromString,
                )
        self.CLIENT_PING = channel.unary_unary(
                '/propius.Load_balancer/CLIENT_PING',
                request_serializer=propius__pb2.client_id.SerializeToString,
                response_deserializer=propius__pb2.cm_offer.FromString,
                )
        self.CLIENT_ACCEPT = channel.unary_unary(
                '/propius.Load_balancer/CLIENT_ACCEPT',
                request_serializer=propius__pb2.client_accept.SerializeToString,
                response_deserializer=propius__pb2.cm_ack.FromString,
                )


class Load_balancerServicer(object):
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

    def CLIENT_ACCEPT(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Load_balancerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CLIENT_CHECKIN': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_CHECKIN,
                    request_deserializer=propius__pb2.client_checkin.FromString,
                    response_serializer=propius__pb2.cm_offer.SerializeToString,
            ),
            'CLIENT_PING': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_PING,
                    request_deserializer=propius__pb2.client_id.FromString,
                    response_serializer=propius__pb2.cm_offer.SerializeToString,
            ),
            'CLIENT_ACCEPT': grpc.unary_unary_rpc_method_handler(
                    servicer.CLIENT_ACCEPT,
                    request_deserializer=propius__pb2.client_accept.FromString,
                    response_serializer=propius__pb2.cm_ack.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'propius.Load_balancer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Load_balancer(object):
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
        return grpc.experimental.unary_unary(request, target, '/propius.Load_balancer/CLIENT_CHECKIN',
            propius__pb2.client_checkin.SerializeToString,
            propius__pb2.cm_offer.FromString,
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
        return grpc.experimental.unary_unary(request, target, '/propius.Load_balancer/CLIENT_PING',
            propius__pb2.client_id.SerializeToString,
            propius__pb2.cm_offer.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CLIENT_ACCEPT(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/propius.Load_balancer/CLIENT_ACCEPT',
            propius__pb2.client_accept.SerializeToString,
            propius__pb2.cm_ack.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
