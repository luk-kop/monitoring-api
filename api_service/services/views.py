from flask import Blueprint, request
from flask_restful import Resource, reqparse

from api_service.extensions import api

# TODO: to delete
from datetime import datetime
from uuid import uuid4


serv_bp = Blueprint('serv_bp', __name__)

parser = reqparse.RequestParser()
parser.add_argument('name', type=str, required=True)
parser.add_argument('price', type=float, required=True)


services_dummy_data = [
    {
        'id': str(uuid4()),
        'name': 'dns-service',
        'host': '1.1.1.1',
        'port': '53',
        'proto': 'udp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    },
    {
        'id': str(uuid4()),
        'name': 'home-ssh-service',
        'host': '192.168.1.1',
        'port': '22',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    },
    {
        'id': str(uuid4()),
        'name': 'home-ntp-service',
        'host': '192.168.1.1',
        'port': '123',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    },
    {
        'id': str(uuid4()),
        'name': 'localhost-nmea-service',
        'host': '172.16.1.126',
        'port': '10110',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    }
]


class Services(Resource):
    def get(self):
        services = services_dummy_data
        return services, 200

    def post(self):
        data = request.get_json()
        services_dummy_data.append(data)
        return {'service': data}, 201


class Service(Resource):
    def get(self, service_id):
        service = next(filter(lambda x: x['id'] == service_id, services_dummy_data), None)
        return {'service': service}, 200 if service else 404

    def put(self, service_id):
        # TODO: change to: data = parser.parse_args()
        data = request.get_json()
        service = next(filter(lambda x: x['id'] == service_id, services_dummy_data), None)
        if service:
            service.update(data)
            return {'service': service}, 200
        else:
            data['id'] = service_id
            services_dummy_data.append(data)
            return {'service': data}, 201

    def delete(self, service_id):
        global services_dummy_data
        services_dummy_data = list(filter(lambda x: x['id'] != service_id, services_dummy_data))
        return {'message': f'item {service_id} deleted'}, 200


api.add_resource(Services, '/services')
api.add_resource(Service, '/services/<string:id>')
