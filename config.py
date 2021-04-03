import os
from pathlib import Path

from dotenv import load_dotenv


basedir = Path(__file__).resolve().parent
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """
    Set base Flask configuration vars.
    """
    # General Config
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_URL'),
    }
    # Default number of documents on page (api results pagination)
    DEFAULT_PAGINATION_LIMIT = 6
    MAX_PAGINATION_LIMIT = 30
    # Flasgger Config
    SWAGGER = {
        'title': 'Monitoring API',
        'description': '### A simple REST API to monitor the availability of selected services. '
                       'The application checks at regular intervals the availability of services on the '
                       'specified ip address (or hostname) and port',
        'version': '1.0.0',
        'uiversion': 3,
        'termsOfService': '',
        # 'specs_route': '/apidocs/'

    }

