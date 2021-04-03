import re

from flask import current_app
from marshmallow import Schema, fields, post_dump, pre_load, validates, ValidationError, validates_schema
from marshmallow.validate import OneOf, Length
from bson import objectid

from api_service.models import Service


class ServiceHostSchema(Schema):
    """
    The schema used as nested field in 'ServiceSchema'.
    """
    type = fields.Str(required=True,
                      error_messages={'required': 'Host type field is required'},
                      validate=OneOf(choices=['hostname', 'ip'],
                                     error='Not valid host type (use ip or hostname)'))
    value = fields.Str(required=True,
                       error_messages={'required': 'Host value field is required'},
                       validate=Length(max=30))

    @validates_schema
    def validate_host(self, data, **kwargs):
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

    class Meta:
        ordered = True


class ServiceTimestampsSchema(Schema):
    """
    The schema used as nested field in 'ServiceSchema'.
    """
    last_responded = fields.DateTime(dump_only=True)
    last_tested = fields.DateTime(dump_only=True)
    created = fields.DateTime(dump_only=True)
    edited = fields.DateTime(dump_only=True)

    @post_dump
    def none_to_string(self, data, **kwargs):
        for key, value in data.items():
            data[key] = '' if value is None else value
        return data

    class Meta:
        ordered = True


class ServiceSchema(Schema):
    """
    The schema for serializing and deserializing 'service' POST (JSON).
    """
    id = fields.Str(dump_only=True)
    name = fields.Str(required=True,
                      error_messages={'required': 'Name field is required'},
                      validate=Length(max=40))
    host = fields.Nested(ServiceHostSchema(),
                         error_messages={'required': 'Host field is required'},
                         required=True)
    proto = fields.Str(required=True,
                       error_messages={'required': 'Proto field is required'},
                       validate=OneOf(choices=['tcp', 'udp'],
                                      error='Not valid protocol. Use tcp or udp'))
    port = fields.Str(required=True,
                      error_messages={'required': 'Port field is required'},
                      validate=Length(max=8))
    timestamps = fields.Nested(ServiceTimestampsSchema(),
                               dump_only=True)
    service_up = fields.Boolean(dump_only=True)

    @pre_load
    def validate_type(self, data, **kwargs):
        if not data or not isinstance(data, dict):
            raise ValidationError('Invalid input type.', 'services')
        if 'host' in data.keys() and not isinstance(data.get('host'), dict):
            raise ValidationError('Invalid input type', 'host')
        return data

    @validates('name')
    def validate_name(self, name):
        if Service.objects(name=name):
            raise ValidationError(f'Service {name} already exists, please use a different name')

    @validates('port')
    def validate_port(self, port):
        try:
            port = int(port)
        except ValueError:
            raise ValidationError('Not valid network port')
        if port not in range(0, 65353):
            raise ValidationError('Not valid network port')

    class Meta:
        ordered = True


class ServiceSchemaQueryParams(Schema):
    """
    The schema for deserializing 'service' query params.
    """
    after = fields.Str()
    before = fields.Str()
    limit = fields.Integer()
    sort=fields.Str()

    @validates('after')
    def validate_after(self, after_id):
        if after_id and not objectid.ObjectId.is_valid(after_id):
            raise ValidationError('Not valid cursor')
        if after_id and not Service.objects(id=after_id):
            raise ValidationError(f'Cursor with id {after_id} does not exist')

    @validates('before')
    def validate_before(self, before_id):
        if before_id and not objectid.ObjectId.is_valid(before_id):
            raise ValidationError('Not valid cursor')
        if before_id and not Service.objects(id=before_id):
            raise ValidationError(f'Cursor with id {before_id} does not exist')

    @validates('limit')
    def validate_limit(self, limit):
        limit_max = current_app.config.get('MAX_PAGINATION_LIMIT')
        if limit not in range(1, limit_max + 1):
            raise ValidationError(f'Not valid limit (limit range 1-{limit_max})')

    @validates('sort')
    def validate_sort(self, value):
        print(value)
        if value and not value == 'name':
            raise ValidationError('Not valid sort value. Use value name.')

    @pre_load
    def validate_data(self, data, **kwargs):
        if 'after' in data.keys() and 'before' in data.keys():
            raise ValidationError('before and after cannot be used together', 'query_params')
        return data


class PagingLinksSchema(Schema):
    """
    The schema perform the serialization of paginate URLs.
    The schema is used as nested field in 'PagingSchema'.
    """
    previous = fields.Url(dump_only=True)
    next = fields.Url(dump_only=True)

    class Meta:
        ordered = True


class PagingCursorsSchema(Schema):
    """
    The schema perform the serialization of cursors data.
    The schema used as nested field in 'PagingSchema'.
    """
    before = fields.Str(dump_only=True)
    after = fields.Str(dump_only=True)

    class Meta:
        ordered = True


class PagingSchema(Schema):
    """
    The schema perform the serialization of pagination data.
    The schema used as nested field in 'ServicesSchema'.
    """
    limit = fields.Integer(dump_only=True)
    cursors = fields.Nested(PagingCursorsSchema())
    links = fields.Nested(PagingLinksSchema())

    class Meta:
        ordered = True


class ServicesDataSchema(Schema):
    """
    The schema perform the serialization of services data.
    The schema used as nested field in 'ServicesSchema'.
    """
    services_total = fields.Integer(dump_only=True)
    services_up = fields.Integer(dump_only=True)
    services = fields.List(fields.Nested(ServiceSchema))

    class Meta:
        ordered = True


class ServicesSchema(Schema):
    """
    The schema for serializing 'services' and paging info.
    """
    paging = fields.Nested(PagingSchema())
    data = fields.Nested(ServicesDataSchema)

    class Meta:
        ordered = True


def error_parser(error):
    """
    Custom error output.
    """
    errors_new = {}
    for field, value in error.messages.items():
        if isinstance(value, dict):
            inside_dict = {}
            for key_in, val_in in value.items():
                if len(val_in) == 1:
                    inside_dict[key_in] = val_in[0]
                else:
                    inside_dict[key_in] = val_in
            errors_new[field] = inside_dict
        else:
            if len(value) == 1:
                errors_new[field] = value[0]
            else:
                errors_new[field] = value
    return errors_new
