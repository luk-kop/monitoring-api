from flask import Blueprint, request
from flask_restful import Resource, reqparse, marshal_with, abort
from bson import objectid
from marshmallow import ValidationError

from api_service.extensions import api
from api_service.models import Service
from api_service.services.fields_custom import service_fields, services_fields
from api_service.services.schemas import ServiceSchema


serv_bp = Blueprint('serv_bp', __name__)


class ServicesApi(Resource):
    @marshal_with(services_fields)
    def get(self):
        services = Service.objects().order_by('name').all()
        services_count = Service.objects().count()
        services_count_up = Service.objects(service_up=True).count()
        response = {
            'services_number': services_count,
            'services_up': services_count_up,
            'services': services,
        }
        # services = [service.to_dict() for service in services]
        return response, 200

    def post(self):
        schema = ServiceSchema()
        request_data = request.get_json()
        print(request)
        print(request_data)
        try:
            result = schema.load(request_data)
        except ValidationError as error:
            abort(400, maessage=error.messages)
        return {'id': str(result.id)}, 201


class ServiceApi(Resource):
    @marshal_with(service_fields, envelope='service')
    def get(self, service_id):
        # Check whether id is 24-character hex string
        if not objectid.ObjectId.is_valid(service_id):
            abort(404, maessage='Not valid id')
        result = Service.objects(id=service_id)
        if not result:
            abort(404, maessage=f'Could not find service with id {service_id}')
        # service = result.first().to_dict()
        service = result.first()
        return service, 200

    # def put(self, service_id):
    #     # TODO: change to: data = parser.parse_args()
    #     data = request.get_json()
    #     service = next(filter(lambda x: x['id'] == service_id, services_dummy_data), None)
    #     if service:
    #         service.update(data)
    #         return {'service': service}, 200
    #     else:
    #         data['id'] = service_id
    #         services_dummy_data.append(data)
    #         return {'service': data}, 201

    def delete(self, service_id):
        # Check whether id is 24-character hex string
        if not objectid.ObjectId.is_valid(service_id):
            abort(404, maessage='Not valid id')
        result = Service.objects(id=service_id)
        if not result:
            abort(404, maessage='Service doesn\'t exist, can\'t delete')
        Service.objects.get(id=service_id).delete()
        return {'message': f'service {service_id} deleted'}, 200


api.add_resource(ServicesApi, '/services')
api.add_resource(ServiceApi, '/services/<string:service_id>')
