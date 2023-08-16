# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: executor.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0e\x65xecutor.proto\x12\x08\x65xecutor\"\"\n\rworker_status\x12\x11\n\ttask_size\x18\x01 \x01(\x05\"8\n\x0btask_result\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\x12\x0e\n\x06result\x18\x02 \x01(\x0c\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\x0c\",\n\x08job_info\x12\x0e\n\x06job_id\x18\x01 \x01(\x05\x12\x10\n\x08job_meta\x18\x02 \x01(\x0c\"v\n\rjob_task_info\x12\x0e\n\x06job_id\x18\x01 \x01(\x05\x12\x11\n\tclient_id\x18\x02 \x01(\x05\x12\r\n\x05round\x18\x03 \x01(\x05\x12\r\n\x05\x65vent\x18\x04 \x01(\t\x12\x11\n\ttask_meta\x18\x05 \x01(\x0c\x12\x11\n\ttask_data\x18\x06 \x01(\x0c\"\x14\n\x06job_id\x12\n\n\x02id\x18\x01 \x01(\x05\"/\n\x0cregister_ack\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\x12\x12\n\nmodel_size\x18\x02 \x01(\x02\"\x12\n\x03\x61\x63k\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\"\x07\n\x05\x65mpty2\x87\x01\n\x08\x45xecutor\x12<\n\x0cJOB_REGISTER\x12\x12.executor.job_info\x1a\x16.executor.register_ack\"\x00\x12=\n\x11JOB_REGISTER_TASK\x12\x17.executor.job_task_info\x1a\r.executor.ack\"\x00\x32\xbd\x02\n\x06Worker\x12+\n\x04INIT\x12\x12.executor.job_info\x1a\r.executor.ack\"\x00\x12-\n\x06REMOVE\x12\x12.executor.job_info\x1a\r.executor.ack\"\x00\x12\x31\n\x05TRAIN\x12\x17.executor.job_task_info\x1a\r.executor.ack\"\x00\x12\x30\n\x04TEST\x12\x17.executor.job_task_info\x1a\r.executor.ack\"\x00\x12\x38\n\x04PING\x12\x17.executor.job_task_info\x1a\x15.executor.task_result\"\x00\x12\x38\n\nHEART_BEAT\x12\x0f.executor.empty\x1a\x17.executor.worker_status\"\x00\x62\x06proto3')



_WORKER_STATUS = DESCRIPTOR.message_types_by_name['worker_status']
_TASK_RESULT = DESCRIPTOR.message_types_by_name['task_result']
_JOB_INFO = DESCRIPTOR.message_types_by_name['job_info']
_JOB_TASK_INFO = DESCRIPTOR.message_types_by_name['job_task_info']
_JOB_ID = DESCRIPTOR.message_types_by_name['job_id']
_REGISTER_ACK = DESCRIPTOR.message_types_by_name['register_ack']
_ACK = DESCRIPTOR.message_types_by_name['ack']
_EMPTY = DESCRIPTOR.message_types_by_name['empty']
worker_status = _reflection.GeneratedProtocolMessageType('worker_status', (_message.Message,), {
  'DESCRIPTOR' : _WORKER_STATUS,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.worker_status)
  })
_sym_db.RegisterMessage(worker_status)

task_result = _reflection.GeneratedProtocolMessageType('task_result', (_message.Message,), {
  'DESCRIPTOR' : _TASK_RESULT,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.task_result)
  })
_sym_db.RegisterMessage(task_result)

job_info = _reflection.GeneratedProtocolMessageType('job_info', (_message.Message,), {
  'DESCRIPTOR' : _JOB_INFO,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.job_info)
  })
_sym_db.RegisterMessage(job_info)

job_task_info = _reflection.GeneratedProtocolMessageType('job_task_info', (_message.Message,), {
  'DESCRIPTOR' : _JOB_TASK_INFO,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.job_task_info)
  })
_sym_db.RegisterMessage(job_task_info)

job_id = _reflection.GeneratedProtocolMessageType('job_id', (_message.Message,), {
  'DESCRIPTOR' : _JOB_ID,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.job_id)
  })
_sym_db.RegisterMessage(job_id)

register_ack = _reflection.GeneratedProtocolMessageType('register_ack', (_message.Message,), {
  'DESCRIPTOR' : _REGISTER_ACK,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.register_ack)
  })
_sym_db.RegisterMessage(register_ack)

ack = _reflection.GeneratedProtocolMessageType('ack', (_message.Message,), {
  'DESCRIPTOR' : _ACK,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.ack)
  })
_sym_db.RegisterMessage(ack)

empty = _reflection.GeneratedProtocolMessageType('empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'executor_pb2'
  # @@protoc_insertion_point(class_scope:executor.empty)
  })
_sym_db.RegisterMessage(empty)

_EXECUTOR = DESCRIPTOR.services_by_name['Executor']
_WORKER = DESCRIPTOR.services_by_name['Worker']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _WORKER_STATUS._serialized_start=28
  _WORKER_STATUS._serialized_end=62
  _TASK_RESULT._serialized_start=64
  _TASK_RESULT._serialized_end=120
  _JOB_INFO._serialized_start=122
  _JOB_INFO._serialized_end=166
  _JOB_TASK_INFO._serialized_start=168
  _JOB_TASK_INFO._serialized_end=286
  _JOB_ID._serialized_start=288
  _JOB_ID._serialized_end=308
  _REGISTER_ACK._serialized_start=310
  _REGISTER_ACK._serialized_end=357
  _ACK._serialized_start=359
  _ACK._serialized_end=377
  _EMPTY._serialized_start=379
  _EMPTY._serialized_end=386
  _EXECUTOR._serialized_start=389
  _EXECUTOR._serialized_end=524
  _WORKER._serialized_start=527
  _WORKER._serialized_end=844
# @@protoc_insertion_point(module_scope)
