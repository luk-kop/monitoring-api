from flask import Blueprint, request
from flask_restful import Resource, marshal_with, abort
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
        services_count_all = Service.objects().count()
        services_count_up = Service.objects(service_up=True).count()
        response = {
            'services_number': services_count_all,
            'services_up': services_count_up,
            'services': services,
        }
        return response, 200

    def post(self):
        schema = ServiceSchema()
        request_data = request.get_json()
        try:
            result = schema.load(request_data)
        except ValidationError as error:
            abort(400, maessage=error.messages)
        return {'id': str(result.id)}, 201


class ServiceApi(Resource):
    @staticmethod
    def check_service_exist(service_id):
        """
        Check whether the service with the specified id exists.
        """
        if not Service.objects(id=service_id):
            abort(404, maessage=f'Service with id {service_id} doesn\'t exist')

    @staticmethod
    def check_id(service_id):
        """
        Check whether id is 24-character hex string.
        """
        if not objectid.ObjectId.is_valid(service_id):
            abort(400, maessage='Not valid id')

    @marshal_with(service_fields, envelope='service')
    def get(self, service_id):
        self.check_id(service_id)
        self.check_service_exist(service_id)
        service = Service.objects(id=service_id).first()
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

    def patch(self, service_id):
        self.check_id(service_id)
        self.check_service_exist(service_id)
        pass

    def delete(self, service_id):
        self.check_id(service_id)
        self.check_service_exist(service_id)
        Service.objects.get(id=service_id).delete()
        return {'message': f'service {service_id} deleted'}, 200


api.add_resource(ServicesApi, '/services')
api.add_resource(ServiceApi, '/services/<string:service_id>')
