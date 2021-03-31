from datetime import datetime

from flask import Blueprint, request, current_app
from flask_restful import Resource, abort
from bson import objectid
from marshmallow import ValidationError

from api_service.extensions import api
from api_service.models import Service
from api_service.services.schemas import ServiceSchema, ServiceSchemaQueryParams, ServicesSchema, error_parser

serv_bp = Blueprint('serv_bp', __name__)


class ServicesApi(Resource):
    def get(self):
        # Deserialize query params
        schema = ServiceSchemaQueryParams()
        try:
            data_query_params = schema.load(request.args)
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            abort(400, message=errors_custom, status=400)
            # return {'message': errors_custom, 'status': 400}, 400
        page_limit_default = current_app.config.get('DEFAULT_PAGINATION_LIMIT')
        after_id = data_query_params.get('after', '')
        before_id = data_query_params.get('before', '')
        page_limit = data_query_params.get('limit', page_limit_default)
        # Get services with custom pagination
        services = Service.paginate_cursor(after_id=after_id, before_id=before_id, page_limit=page_limit)
        # Get next page url
        if services.after:
            next_url = api.url_for(ServicesApi,
                                   limit=page_limit if page_limit else '',
                                   after=services.after.id,
                                   _external=True)
        else:
            next_url = ''
        # Get prev page url
        if services.before:
            prev_url = api.url_for(ServicesApi,
                                   limit=page_limit if page_limit else '',
                                   before=services.before.id,
                                   _external=True)
        else:
            prev_url = ''
        # Get number of running services
        services_count_up = Service.objects(service_up=True).count()

        # Prepare data to dump
        paging = {
            'limit': page_limit,
            'cursors': {
                'before': str(services.before.id) if services.before else '',
                'after': str(services.after.id) if services.after else ''
            },
            'links': {
                'previous': prev_url,
                'next': next_url
            }
        }
        data = {
            'services_total': services.total,
            'services_up': services_count_up,
            'services': services.items,
        }
        services_to_dump = {
            'paging': paging,
            'data': data
        }
        # Serialize services with paging info
        schema = ServicesSchema()
        dumped_services = schema.dump(services_to_dump)
        return dumped_services, 200

    def post(self):
        schema = ServiceSchema()
        request_data = request.get_json()
        try:
            result = schema.load(request_data)
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            return {'message': errors_custom, 'status': 400}, 400
        service = Service(**result).save()
        return {'id': str(service.id)}, 201


class ServiceApi(Resource):
    @staticmethod
    def check_id(service_id):
        """
        Check whether id is 24-character hex string.
        """
        if not objectid.ObjectId.is_valid(service_id):
            abort(400, message='Not valid id', status=400)

    def get(self, service_id):
        self.check_id(service_id)
        service = Service.objects(id=service_id).first()
        if not service:
            abort(404, message=f'Service with id {service_id} doesn\'t exist', status=404)
        schema = ServiceSchema()
        dumped_service = schema.dump(service)
        return {'service': dumped_service}, 200

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
        service = Service.objects(id=service_id).first()
        if not service:
            abort(404, message=f'Service with id {service_id} doesn\'t exist', status=404)
        schema = ServiceSchema()
        request_data = request.get_json()
        try:
            result = schema.load(request_data, partial=('name', 'host', 'port', 'proto'))
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            return {'message': errors_custom, 'status': 406}, 406
        if result.get('name'):
            service.name = result['name']
        if result.get('host'):
            if result['host']['type']:
                service.host.type = result['host']['type']
            if result['host']['value']:
                service.host.value = result['host']['value']
        if result.get('port'):
            service.port = result['port']
        if result.get('proto'):
            service.proto = result['proto']
        service.timestamps.edited = datetime.utcnow()
        service.save()
        dumped_service = schema.dump(service)
        return {'service': dumped_service}, 200

    def delete(self, service_id):
        self.check_id(service_id)
        service = Service.objects(id=service_id).first()
        if not service:
            abort(404, message=f'Service with id {service_id} doesn\'t exist', status=404)
        service.delete()
        return {'message': f'Service {service_id} deleted'}, 200
