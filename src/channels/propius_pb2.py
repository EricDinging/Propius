# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: propius.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rpropius.proto\x12\x07propius\"A\n\x0e\x63lient_checkin\x12\x11\n\tclient_id\x18\x01 \x01(\x05\x12\x1c\n\x14public_specification\x18\x02 \x01(\x0c\":\n\x08\x63m_offer\x12\x12\n\ntask_offer\x18\x01 \x01(\x0c\x12\x1a\n\x12private_constraint\x18\x02 \x01(\x0c\"3\n\rclient_accept\x12\x11\n\tclient_id\x18\x01 \x01(\x05\x12\x0f\n\x07task_id\x18\x02 \x01(\x05\"7\n\x06\x63m_ack\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\x12\x0e\n\x06job_ip\x18\x02 \x01(\x0c\x12\x10\n\x08job_port\x18\x03 \x01(\x05\"\x18\n\x04plan\x12\x10\n\x08workload\x18\x01 \x01(\x05\"\x17\n\tclient_id\x12\n\n\x02id\x18\x01 \x01(\x05\"\x14\n\x06job_id\x12\n\n\x02id\x18\x01 \x01(\x05\"o\n\x08job_info\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x14\n\x0ctotal_demand\x18\x02 \x01(\x05\x12\x13\n\x0btotal_round\x18\x03 \x01(\x05\x12\x12\n\nconstraint\x18\x04 \x01(\x0c\x12\n\n\x02ip\x18\x05 \x01(\x0c\x12\x0c\n\x04port\x18\x06 \x01(\x05\",\n\x0ejob_round_info\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0e\n\x06\x64\x65mand\x18\x02 \x01(\x05\"2\n\rclient_report\x12\x11\n\tclient_id\x18\x01 \x01(\x05\x12\x0e\n\x06result\x18\x02 \x01(\x02\"\x07\n\x05\x65mpty\"\x12\n\x03\x61\x63k\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\x32w\n\x03Job\x12\x35\n\x0e\x43LIENT_REQUEST\x12\x12.propius.client_id\x1a\r.propius.plan\"\x00\x12\x39\n\rCLIENT_REPORT\x12\x16.propius.client_report\x1a\x0e.propius.empty\"\x00\x32\xa7\x01\n\x0bJob_manager\x12/\n\nJOB_REGIST\x12\x11.propius.job_info\x1a\x0c.propius.ack\"\x00\x12\x36\n\x0bJOB_REQUEST\x12\x17.propius.job_round_info\x1a\x0c.propius.ack\"\x00\x12/\n\nJOB_FINISH\x12\x0f.propius.job_id\x1a\x0e.propius.empty\"\x00\x32@\n\tScheduler\x12\x33\n\x10JOB_SCORE_UPDATE\x12\x0f.propius.job_id\x1a\x0c.propius.ack\"\x00\x32\x8c\x01\n\x0e\x43lient_manager\x12>\n\x0e\x43LIENT_CHECKIN\x12\x17.propius.client_checkin\x1a\x11.propius.cm_offer\"\x00\x12:\n\rCLIENT_ACCEPT\x12\x16.propius.client_accept\x1a\x0f.propius.cm_ack\"\x00\x62\x06proto3')



_CLIENT_CHECKIN = DESCRIPTOR.message_types_by_name['client_checkin']
_CM_OFFER = DESCRIPTOR.message_types_by_name['cm_offer']
_CLIENT_ACCEPT = DESCRIPTOR.message_types_by_name['client_accept']
_CM_ACK = DESCRIPTOR.message_types_by_name['cm_ack']
_PLAN = DESCRIPTOR.message_types_by_name['plan']
_CLIENT_ID = DESCRIPTOR.message_types_by_name['client_id']
_JOB_ID = DESCRIPTOR.message_types_by_name['job_id']
_JOB_INFO = DESCRIPTOR.message_types_by_name['job_info']
_JOB_ROUND_INFO = DESCRIPTOR.message_types_by_name['job_round_info']
_CLIENT_REPORT = DESCRIPTOR.message_types_by_name['client_report']
_EMPTY = DESCRIPTOR.message_types_by_name['empty']
_ACK = DESCRIPTOR.message_types_by_name['ack']
client_checkin = _reflection.GeneratedProtocolMessageType('client_checkin', (_message.Message,), {
  'DESCRIPTOR' : _CLIENT_CHECKIN,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.client_checkin)
  })
_sym_db.RegisterMessage(client_checkin)

cm_offer = _reflection.GeneratedProtocolMessageType('cm_offer', (_message.Message,), {
  'DESCRIPTOR' : _CM_OFFER,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.cm_offer)
  })
_sym_db.RegisterMessage(cm_offer)

client_accept = _reflection.GeneratedProtocolMessageType('client_accept', (_message.Message,), {
  'DESCRIPTOR' : _CLIENT_ACCEPT,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.client_accept)
  })
_sym_db.RegisterMessage(client_accept)

cm_ack = _reflection.GeneratedProtocolMessageType('cm_ack', (_message.Message,), {
  'DESCRIPTOR' : _CM_ACK,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.cm_ack)
  })
_sym_db.RegisterMessage(cm_ack)

plan = _reflection.GeneratedProtocolMessageType('plan', (_message.Message,), {
  'DESCRIPTOR' : _PLAN,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.plan)
  })
_sym_db.RegisterMessage(plan)

client_id = _reflection.GeneratedProtocolMessageType('client_id', (_message.Message,), {
  'DESCRIPTOR' : _CLIENT_ID,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.client_id)
  })
_sym_db.RegisterMessage(client_id)

job_id = _reflection.GeneratedProtocolMessageType('job_id', (_message.Message,), {
  'DESCRIPTOR' : _JOB_ID,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.job_id)
  })
_sym_db.RegisterMessage(job_id)

job_info = _reflection.GeneratedProtocolMessageType('job_info', (_message.Message,), {
  'DESCRIPTOR' : _JOB_INFO,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.job_info)
  })
_sym_db.RegisterMessage(job_info)

job_round_info = _reflection.GeneratedProtocolMessageType('job_round_info', (_message.Message,), {
  'DESCRIPTOR' : _JOB_ROUND_INFO,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.job_round_info)
  })
_sym_db.RegisterMessage(job_round_info)

client_report = _reflection.GeneratedProtocolMessageType('client_report', (_message.Message,), {
  'DESCRIPTOR' : _CLIENT_REPORT,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.client_report)
  })
_sym_db.RegisterMessage(client_report)

empty = _reflection.GeneratedProtocolMessageType('empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.empty)
  })
_sym_db.RegisterMessage(empty)

ack = _reflection.GeneratedProtocolMessageType('ack', (_message.Message,), {
  'DESCRIPTOR' : _ACK,
  '__module__' : 'propius_pb2'
  # @@protoc_insertion_point(class_scope:propius.ack)
  })
_sym_db.RegisterMessage(ack)

_JOB = DESCRIPTOR.services_by_name['Job']
_JOB_MANAGER = DESCRIPTOR.services_by_name['Job_manager']
_SCHEDULER = DESCRIPTOR.services_by_name['Scheduler']
_CLIENT_MANAGER = DESCRIPTOR.services_by_name['Client_manager']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CLIENT_CHECKIN._serialized_start=26
  _CLIENT_CHECKIN._serialized_end=91
  _CM_OFFER._serialized_start=93
  _CM_OFFER._serialized_end=151
  _CLIENT_ACCEPT._serialized_start=153
  _CLIENT_ACCEPT._serialized_end=204
  _CM_ACK._serialized_start=206
  _CM_ACK._serialized_end=261
  _PLAN._serialized_start=263
  _PLAN._serialized_end=287
  _CLIENT_ID._serialized_start=289
  _CLIENT_ID._serialized_end=312
  _JOB_ID._serialized_start=314
  _JOB_ID._serialized_end=334
  _JOB_INFO._serialized_start=336
  _JOB_INFO._serialized_end=447
  _JOB_ROUND_INFO._serialized_start=449
  _JOB_ROUND_INFO._serialized_end=493
  _CLIENT_REPORT._serialized_start=495
  _CLIENT_REPORT._serialized_end=545
  _EMPTY._serialized_start=547
  _EMPTY._serialized_end=554
  _ACK._serialized_start=556
  _ACK._serialized_end=574
  _JOB._serialized_start=576
  _JOB._serialized_end=695
  _JOB_MANAGER._serialized_start=698
  _JOB_MANAGER._serialized_end=865
  _SCHEDULER._serialized_start=867
  _SCHEDULER._serialized_end=931
  _CLIENT_MANAGER._serialized_start=934
  _CLIENT_MANAGER._serialized_end=1074
# @@protoc_insertion_point(module_scope)
