from flask_restful import fields


host_field = {
    'type': fields.String,
    'value': fields.String
}

timestamps_field = {
    'last_responded': fields.DateTime(dt_format='iso8601', default=''),
    'last_tested': fields.DateTime(dt_format='iso8601', default=''),
    'created': fields.DateTime(dt_format='iso8601'),
    'edited': fields.DateTime(dt_format='iso8601', default='')
}

links_field = {
    'prev_url': fields.String,
    'self_url': fields.String,
    'next_url': fields.String
}

service_fields = {
    'id': fields.String,
    'name': fields.String,
    'host': fields.Nested(host_field),
    'proto': fields.String,
    'port': fields.String,
    'timestamps': fields.Nested(timestamps_field),
    'service_up': fields.Boolean
}

services_fields = {
    'links': fields.Nested(links_field),
    'limit': fields.Integer,
    'services_total': fields.Integer,
    'services_up': fields.Integer,
    'services': fields.List(fields.Nested(service_fields)),
}
