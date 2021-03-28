from flask_restful import Api
from flask_mongoengine import MongoEngine

from api_service.services.errors import errors as errors_custom

api = Api(catch_all_404s=True, errors=errors_custom)
db = MongoEngine()
