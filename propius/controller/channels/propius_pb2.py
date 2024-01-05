# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: propius.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rpropius.proto\x12\x07propius\".\n\x0e\x63lient_checkin\x12\x1c\n\x14public_specification\x18\x01 \x01(\x0c\"d\n\x08\x63m_offer\x12\x11\n\tclient_id\x18\x01 \x01(\x05\x12\x12\n\ntask_offer\x18\x02 \x01(\x0c\x12\x1a\n\x12private_constraint\x18\x03 \x01(\x0c\x12\x15\n\rtotal_job_num\x18\x04 \x01(\x05\"\x1b\n\ngroup_info\x12\r\n\x05group\x18\x01 \x01(\x0c\"3\n\rclient_accept\x12\x11\n\tclient_id\x18\x01 \x01(\x05\x12\x0f\n\x07task_id\x18\x02 \x01(\x05\"F\n\x06\x63m_ack\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\x12\x0e\n\x06job_ip\x18\x02 \x01(\x0c\x12\x10\n\x08job_port\x18\x03 \x01(\x05\x12\r\n\x05round\x18\x04 \x01(\x05\"$\n\x06jm_ack\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\x12\r\n\x05round\x18\x02 \x01(\x05\"\x17\n\tclient_id\x12\n\n\x02id\x18\x01 \x01(\x05\"\x14\n\x06job_id\x12\n\n\x02id\x18\x01 \x01(\x05\"\x88\x01\n\x08job_info\x12\x12\n\nest_demand\x18\x01 \x01(\x05\x12\x17\n\x0f\x65st_total_round\x18\x02 \x01(\x05\x12\x19\n\x11public_constraint\x18\x03 \x01(\x0c\x12\x1a\n\x12private_constraint\x18\x04 \x01(\x0c\x12\n\n\x02ip\x18\x05 \x01(\x0c\x12\x0c\n\x04port\x18\x06 \x01(\x05\",\n\x0ejob_round_info\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0e\n\x06\x64\x65mand\x18\x02 \x01(\x05\"\x07\n\x05\x65mpty\"+\n\x10job_register_ack\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0b\n\x03\x61\x63k\x18\x02 \x01(\x08\"\x12\n\x03\x61\x63k\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\x08\x32\x99\x02\n\x0bJob_manager\x12<\n\nJOB_REGIST\x12\x11.propius.job_info\x1a\x19.propius.job_register_ack\"\x00\x12\x39\n\x0bJOB_REQUEST\x12\x17.propius.job_round_info\x1a\x0f.propius.jm_ack\"\x00\x12\x32\n\x0fJOB_END_REQUEST\x12\x0f.propius.job_id\x1a\x0c.propius.ack\"\x00\x12/\n\nJOB_FINISH\x12\x0f.propius.job_id\x1a\x0e.propius.empty\"\x00\x12,\n\nHEART_BEAT\x12\x0e.propius.empty\x1a\x0c.propius.ack\"\x00\x32\xd0\x01\n\tScheduler\x12-\n\nJOB_REGIST\x12\x0f.propius.job_id\x1a\x0c.propius.ack\"\x00\x12.\n\x0bJOB_REQUEST\x12\x0f.propius.job_id\x1a\x0c.propius.ack\"\x00\x12\x36\n\rGET_JOB_GROUP\x12\x0e.propius.empty\x1a\x13.propius.group_info\"\x00\x12,\n\nHEART_BEAT\x12\x0e.propius.empty\x1a\x0c.propius.ack\"\x00\x32\xf2\x01\n\x0e\x43lient_manager\x12>\n\x0e\x43LIENT_CHECKIN\x12\x17.propius.client_checkin\x1a\x11.propius.cm_offer\"\x00\x12\x36\n\x0b\x43LIENT_PING\x12\x12.propius.client_id\x1a\x11.propius.cm_offer\"\x00\x12:\n\rCLIENT_ACCEPT\x12\x16.propius.client_accept\x1a\x0f.propius.cm_ack\"\x00\x12,\n\nHEART_BEAT\x12\x0e.propius.empty\x1a\x0c.propius.ack\"\x00\x32\xf1\x01\n\rLoad_balancer\x12>\n\x0e\x43LIENT_CHECKIN\x12\x17.propius.client_checkin\x1a\x11.propius.cm_offer\"\x00\x12\x36\n\x0b\x43LIENT_PING\x12\x12.propius.client_id\x1a\x11.propius.cm_offer\"\x00\x12:\n\rCLIENT_ACCEPT\x12\x16.propius.client_accept\x1a\x0f.propius.cm_ack\"\x00\x12,\n\nHEART_BEAT\x12\x0e.propius.empty\x1a\x0c.propius.ack\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'propius_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _CLIENT_CHECKIN._serialized_start=26
  _CLIENT_CHECKIN._serialized_end=72
  _CM_OFFER._serialized_start=74
  _CM_OFFER._serialized_end=174
  _GROUP_INFO._serialized_start=176
  _GROUP_INFO._serialized_end=203
  _CLIENT_ACCEPT._serialized_start=205
  _CLIENT_ACCEPT._serialized_end=256
  _CM_ACK._serialized_start=258
  _CM_ACK._serialized_end=328
  _JM_ACK._serialized_start=330
  _JM_ACK._serialized_end=366
  _CLIENT_ID._serialized_start=368
  _CLIENT_ID._serialized_end=391
  _JOB_ID._serialized_start=393
  _JOB_ID._serialized_end=413
  _JOB_INFO._serialized_start=416
  _JOB_INFO._serialized_end=552
  _JOB_ROUND_INFO._serialized_start=554
  _JOB_ROUND_INFO._serialized_end=598
  _EMPTY._serialized_start=600
  _EMPTY._serialized_end=607
  _JOB_REGISTER_ACK._serialized_start=609
  _JOB_REGISTER_ACK._serialized_end=652
  _ACK._serialized_start=654
  _ACK._serialized_end=672
  _JOB_MANAGER._serialized_start=675
  _JOB_MANAGER._serialized_end=956
  _SCHEDULER._serialized_start=959
  _SCHEDULER._serialized_end=1167
  _CLIENT_MANAGER._serialized_start=1170
  _CLIENT_MANAGER._serialized_end=1412
  _LOAD_BALANCER._serialized_start=1415
  _LOAD_BALANCER._serialized_end=1656
# @@protoc_insertion_point(module_scope)
