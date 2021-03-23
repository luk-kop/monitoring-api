import re

from marshmallow import Schema, fields, post_load, validates, ValidationError, validates_schema
from marshmallow.validate import OneOf

from api_service.models import Service


class HostSchema(Schema):
    """
    Schema used as nested field in 'ServiceSchema'.
    """
    type = fields.Str(required=True,
                      error_messages={"required": "Host type is required."},
                      validate=OneOf(choices=['hostname', 'ip'],
                                     error='Not valid host type. Use ip or hostname'))
    value = fields.Str(required=True,
                       error_messages={"required": "Host value is required."})

    @validates_schema
    def validate_value(self, data, ** kwargs):
        if data['type'] == 'hostname':
            pattern = r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*' \
                      r'([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'
            mo = re.match(pattern, data['value'])
            if not mo:
                raise ValidationError({'value': ['Not valid hostname']})
        else:
            # Regex matches only unicast IP addresses from range 0.0.0.0 - 223.255.255.255
            pattern = r'^((22[0-3]\.|2[0-1][0-9]\.|[0-1][0-9]{2}\.|[0-9]{1,2}\.)' \
                      r'(25[0-5]\.|2[0-4][0-9]\.|[0-1][0-9]{2}\.|[0-9]{1,2}\.){2}' \
                      r'(25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{1,2}))$'
            mo = re.match(pattern, data['value'])
            if not mo:
                raise ValidationError({'value': ['Not valid ip address']})


class ServiceSchema(Schema):
    """
    Schema for serializing 'service' POST (JSON).
    """
    name = fields.Str(required=True,
                      error_messages={"required": "name is required"})
    host = fields.Nested(HostSchema())
    port = fields.Str(required=True,
                      error_messages={"required": "port is required"})
    proto = fields.Str(required=True,
                       error_messages={"required": "proto is required"},
                       validate=OneOf(choices=['tcp', 'udp'],
                                      error='Not valid protocol. Use tcp or udp'))

    @validates('name')
    def validate_name(self, name):
        if Service.objects(name=name):
            raise ValidationError(f'Service {name} name already exists, please use a different name')

    @validates('port')
    def validate_port(self, port):
        try:
            port = int(port)
        except ValueError:
            raise ValidationError('Not valid network port')
        if port not in range(0, 65353):
            raise ValidationError('Not valid network port')

    @post_load
    def create_service(self, data, **kwargs):
        return Service(**data).save()
