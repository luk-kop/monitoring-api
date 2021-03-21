from flask import Blueprint
from flask_restful import Resource, reqparse, fields, marshal_with, abort
from bson import objectid

from api_service.extensions import api
from api_service.models import Service


serv_bp = Blueprint('serv_bp', __name__)

parser = reqparse.RequestParser()
parser.add_argument('name', type=str, required=True)
parser.add_argument('price', type=float, required=True)


resource_fileds = {
    'id': fields.String,
    'name': fields.String,
    'host': fields.String,
    'proto': fields.String,
    'last_responded': fields.DateTime,
    'last_configured': fields.DateTime,
    'likes': fields.Boolean
}


class ServicesApi(Resource):
    # @marshal_with(resource_fileds)
    def get(self):
        services = Service.objects().order_by('name').all()
        services = [service.to_dict() for service in services]
        return services, 200

    # def post(self):
    #     data = request.get_json()
    #     service = Service(**data).save()
    #     id = service.id
    #     return {'id': str(id)}, 201


class ServiceApi(Resource):
    def get(self, service_id):
        # Check whether id is 24-character hex string
        if not objectid.ObjectId.is_valid(service_id):
            abort(404, maessage='Not valid id')
        result = Service.objects(id=service_id)
        if not result:
            abort(404, maessage=f'Could not find service with id {service_id}')
        service = Service.objects.get(id=service_id).to_dict()
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
