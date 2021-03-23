from flask_restful import fields


service_fields = {
    'id': fields.String,
    'name': fields.String,
    'host': fields.String,
    'proto': fields.String,
    'port': fields.String,
    'last_responded': fields.DateTime(dt_format='iso8601'),
    'last_configured': fields.DateTime(dt_format='iso8601'),
    'service_up': fields.Boolean
}

services_fields = {
    'services_number': fields.Integer,
    'services_up': fields.Integer,
    'services': fields.List(fields.Nested(service_fields)),
}
