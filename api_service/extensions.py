from flask_restful import Api
from flask_mongoengine import MongoEngine
from flasgger import Swagger
from celery import Celery

from api_service.services.errors import errors as errors_custom

api = Api(catch_all_404s=True, errors=errors_custom)
db = MongoEngine()
swag = Swagger()
celery = Celery()