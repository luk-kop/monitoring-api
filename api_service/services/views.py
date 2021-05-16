from datetime import datetime
from uuid import uuid4

from flask import Blueprint, request
from flask_restful import Resource
from marshmallow import ValidationError
from flasgger import swag_from

from api_service.models import Service
from api_service.services.schemas import (
    ServiceSchema,
    ServiceSchemaQueryParams,
    ServicesSchema,
    error_parser,
    WatchdogSchema
)
from api_service.services.utils import (
    set_services_query_params,
    get_services_to_dump,
    check_mongo_id,
    check_service_exist,
    get_watchdog_job
)

serv_bp = Blueprint('serv_bp', __name__)


class ServicesApi(Resource):
    @swag_from("swagger/services_get.yml")
    def get(self):
        """
        Retrieve paginated services and pagination info.
        """
        # Deserialize query params
        schema = ServiceSchemaQueryParams()
        if request.args:
            try:
                data_query_params = schema.load(request.args)
            except ValidationError as error:
                # Custom error output
                errors_custom = error_parser(error)
                return {'message': errors_custom, 'status': 400}, 400
        else:
            data_query_params = {}
        # Set query params
        query_params = set_services_query_params(data_query_params)
        # Get services with custom pagination
        services = Service.paginate_cursor(**query_params)
        # Prepare data to dump
        services_to_dump = get_services_to_dump(resource=ServicesApi, services=services, query_params=query_params)
        # Serialize services with paging info
        schema = ServicesSchema()
        dumped_services = schema.dump(services_to_dump)
        return dumped_services, 200

    @swag_from("swagger/services_post.yml")
    def post(self):
        """
        Add new service to db.
        """
        schema = ServiceSchema()
        request_data = request.get_json()
        try:
            result = schema.load(request_data)
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            return {'message': errors_custom, 'status': 400}, 400
        service = Service(**result).save()
        return {'id': str(service.id)}, 201, {'Location': f'{request.base_url}/{str(service.id)}'}

    @swag_from("swagger/services_delete.yml")
    def delete(self):
        """
        Delete all services from db.
        """
        Service.objects().all().delete()
        return {'message': 'All services deleted'}, 200


class ServiceApi(Resource):
    @swag_from("swagger/service_get.yml")
    def get(self, service_id):
        """
        Retrieve detailed information on the selected service.
        """
        check_mongo_id(service_id)
        service = check_service_exist(service_id)
        schema = ServiceSchema()
        dumped_service = schema.dump(service)
        return {'service': dumped_service}, 200

    @swag_from("swagger/service_put.yml")
    def put(self, service_id):
        """
        Replace the specified service (if it exists).
        Full update to an existing resource.
        """
        check_mongo_id(service_id)
        service = check_service_exist(service_id)
        request_data = request.get_json()
        schema = ServiceSchema()
        try:
            if service.name == request_data.get('name'):
                # If same 'name' in request and db - use a dummy name to omit same name and no data validation.
                request_data['name'] = uuid4().hex
                result = schema.load(request_data)
                result['name'] = service.name
            else:
                result = schema.load(request_data)
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            return {'message': errors_custom, 'status': 400}, 400
        # Update MongoDB document
        service.name = result['name']
        service.host.type = result['host']['type']
        service.host.value = result['host']['value']
        service.proto = result['proto']
        service.port = result['port']
        service.timestamps.edited = datetime.utcnow()
        service.save()
        dumped_service = schema.dump(service)
        return {'service': dumped_service}, 200

    @swag_from("swagger/service_patch.yml")
    def patch(self, service_id):
        """
        Update selected details of specified service (if it exists).
        Partial update to an existing resource.
        """
        check_mongo_id(service_id)
        service = check_service_exist(service_id)
        schema = ServiceSchema()
        request_data = request.get_json()
        try:
            if service.name == request_data.get('name'):
                # If same 'name' in request and db - use a dummy name to omit same name and no data validation.
                request_data['name'] = uuid4().hex
                result = schema.load(request_data, partial=('name', 'host', 'port', 'proto'))
                result['name'] = service.name
            else:
                result = schema.load(request_data, partial=('name', 'host', 'port', 'proto'))
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            return {'message': errors_custom, 'status': 400}, 400
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

    @swag_from("swagger/service_delete.yml")
    def delete(self, service_id):
        """
        Delete the specified service (if it exists).
        """
        check_mongo_id(service_id)
        service = check_service_exist(service_id)
        service.delete()
        return {'message': f'Service with id {service_id} deleted.'}, 200


class WatchdogApi(Resource):
    @swag_from("swagger/watchdog_get.yml")
    def get(self):
        """
        Return information whether the watchdog service is running.
        """
        watchdog_job = get_watchdog_job()
        if watchdog_job.enabled:
            return {'watchdog_status': 'up'}, 200
        else:
            return {'watchdog_status': 'down'}, 200

    @swag_from("swagger/watchdog_post.yml")
    def post(self):
        """
        Start or stop the watchdog service.
        """
        request_data = request.get_json()
        schema = WatchdogSchema()
        try:
            result = schema.load(request_data)
        except ValidationError as error:
            # Custom error output
            errors_custom = error_parser(error)
            return {'message': errors_custom, 'status': 400}, 400
        watchdog_data = result.get('watchdog')
        watchdog_job = get_watchdog_job()
        if watchdog_job.enabled and watchdog_data == 'start':
            return {'message': 'The watchdog is already running.', 'status': 400}, 400
        elif watchdog_job.enabled and watchdog_data == 'stop':
            watchdog_job.disable_job()
            return {'message': 'The watchdog has been stopped.'}, 200
        elif not watchdog_job.enabled and watchdog_data == 'start':
            watchdog_job.enable_job()
            return {'message': 'The watchdog has been activated.'}, 201
        return {'message': 'The watchdog is not running', 'status': 400}, 400

