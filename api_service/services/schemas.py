from marshmallow import Schema, fields, post_load, validates, ValidationError
from marshmallow.validate import OneOf

from api_service.models import Service


class ServiceSchema(Schema):
    name = fields.Str(required=True,
                      error_messages={"required": "name is required"})
    host = fields.Str(required=True,
                      error_messages={"required": "host is required."})
    port = fields.Str(required=True,
                      error_messages={"required": "port is required."})
    proto = fields.Str(required=True,
                       error_messages={"required": "proto is required."},
                       validate=OneOf(choices=['tcp', 'udp'],
                                      error='Not valid protocol. Use tcp or udp'))

    @validates('name')
    def validate_name(self, name):
        if Service.objects(name=name):
            raise ValidationError(f'Service {name} name already exists, please use a different name')

    @validates('host')
    def validate_host(self, name):
        pass

    @validates('port')
    def validate_port(self, port):
        print(port)
        try:
            port = int(port)
        except ValueError:
            raise ValidationError('Not valid network port')
        if port not in range(0, 65353):
            raise ValidationError('Not valid network port')

    # @validates('proto')
    # def validate_proto(self, proto):
    #     if proto not in ['tcp', 'udp']:
    #         raise ValidationError('Not valid protocol. Use tcp or udp')

    @post_load
    def create_service(self, data, **kwargs):
        return Service(**data).save()
