from flask import Blueprint, request, current_app
from flask_restful import Resource, marshal_with, abort, url_for
from bson import objectid
from marshmallow import ValidationError

from api_service.extensions import api
from api_service.models import Service
from api_service.services.fields_custom import service_fields, services_fields
from api_service.services.schemas import ServiceSchema, GetServiceSchema, error_parser


serv_bp = Blueprint('serv_bp', __name__)


class ServicesApi(Resource):
    @marshal_with(services_fields)
    def get(self):
        # Deserialize query params
        schema = GetServiceSchema()
        try:
            data_query_params = schema.load(request.args)
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            abort(400, message=errors_custom , status=400)
        page_limit_default = current_app.config.get('DEFAULT_PAGINATION_LIMIT')
        next_id = data_query_params.get('next', '')
        page_limit = data_query_params.get('limit', page_limit_default)
        # Get services with custom pagination
        services = Service.paginate_custom(next_id=next_id, page_limit=page_limit)
        # Get next page url
        if services.next:
            next_url = api.url_for(ServicesApi, limit=page_limit if page_limit else '', next=services.next.id, _external=True)
        else:
            next_url = ''
        # Get number of running services
        services_count_up = Service.objects(service_up=True).count()
        links = {
            'next': next_url,
            'self': request.url
        }
        dumped_services = {
            '_links': links,
            'limit': page_limit,
            'services_total': services.total,
            'services_up': services_count_up,
            'services': services.items,
        }
        return dumped_services, 200

    def post(self):
        schema = ServiceSchema()
        request_data = request.get_json()
        try:
            result = schema.load(request_data)
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            abort(400, message=errors_custom, status=400)
        return {'id': str(result.id)}, 201


class ServiceApi(Resource):
    @staticmethod
    def check_id(service_id):
        """
        Check whether id is 24-character hex string.
        """
        if not objectid.ObjectId.is_valid(service_id):
            abort(400, message='Not valid id', status=400)

    @marshal_with(service_fields, envelope='service')
    def get(self, service_id):
        self.check_id(service_id)
        service = Service.objects(id=service_id).first()
        if not service:
            abort(404, message=f'Service with id {service_id} doesn\'t exist', status=404)
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

    # def patch(self, service_id):
    #     self.check_id(service_id)
    #     request_data = request.get_json()
    #     if not request_data:
    #         abort(400, message='No input data provided', status=400)
    #     service = Service.objects(id=service_id).first()
    #     if 'name' in request_data.keys() and request_data['name']:
    #         service_name = request_data['name']
    #         if Service.objects(name=service_name):
    #             abort(404, message=f'Service with name {service_name} already exists', status=404)
    #         service.name = service_name
    #     if 'port' in request_data.keys():
    #         pass
    #     if 'proto' in request_data.keys():
    #         pass
    #     if 'host' in request_data.keys():
    #         pass
    #
    #     schema = ServiceSchema()
    #     errors = schema.validate(request_data)
    #     if errors:
    #         return errors
    #     service = Service.objects(id=service_id).first()

    def delete(self, service_id):
        self.check_id(service_id)
        self.check_service_exist(service_id)
        service = Service.objects(id=service_id).find()
        if not service:
            abort(404, message=f'Service with id {service_id} doesn\'t exist', status=404)
        service.delete()
        return {'message': f'Service {service_id} deleted'}, 200



