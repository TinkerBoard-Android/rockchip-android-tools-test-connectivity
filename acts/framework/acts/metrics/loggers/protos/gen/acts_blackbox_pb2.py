# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: acts_blackbox.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='acts_blackbox.proto',
  package='acts.metrics.blackbox',
  syntax='proto2',
  serialized_options=_b('\n!com.android.acts.metrics.blackbox'),
  serialized_pb=_b('\n\x13\x61\x63ts_blackbox.proto\x12\x15\x61\x63ts.metrics.blackbox\"]\n\x18\x41\x63tsBlackboxMetricResult\x12\x17\n\x0ftest_identifier\x18\x01 \x01(\t\x12\x12\n\nmetric_key\x18\x03 \x02(\t\x12\x14\n\x0cmetric_value\x18\x04 \x02(\x01\x42#\n!com.android.acts.metrics.blackbox')
)




_ACTSBLACKBOXMETRICRESULT = _descriptor.Descriptor(
  name='ActsBlackboxMetricResult',
  full_name='acts.metrics.blackbox.ActsBlackboxMetricResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='test_identifier', full_name='acts.metrics.blackbox.ActsBlackboxMetricResult.test_identifier', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='metric_key', full_name='acts.metrics.blackbox.ActsBlackboxMetricResult.metric_key', index=1,
      number=3, type=9, cpp_type=9, label=2,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='metric_value', full_name='acts.metrics.blackbox.ActsBlackboxMetricResult.metric_value', index=2,
      number=4, type=1, cpp_type=5, label=2,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=46,
  serialized_end=139,
)

DESCRIPTOR.message_types_by_name['ActsBlackboxMetricResult'] = _ACTSBLACKBOXMETRICRESULT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ActsBlackboxMetricResult = _reflection.GeneratedProtocolMessageType('ActsBlackboxMetricResult', (_message.Message,), dict(
  DESCRIPTOR = _ACTSBLACKBOXMETRICRESULT,
  __module__ = 'acts_blackbox_pb2'
  # @@protoc_insertion_point(class_scope:acts.metrics.blackbox.ActsBlackboxMetricResult)
  ))
_sym_db.RegisterMessage(ActsBlackboxMetricResult)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
