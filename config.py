import os
from pathlib import Path

from dotenv import load_dotenv
from celery import schedules


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
    # Default number of documents on page (api results pagination)
    DEFAULT_PAGINATION_LIMIT = 6
    MAX_PAGINATION_LIMIT = 30
    # Flasgger Config
    SWAGGER = {
        'title': 'Monitoring API',
        'description': '### The Monitoring API is a simple REST API based on Flask-RESTful library. '
                       'The main purpose of the application is to monitor the availability of selected services. '
                       'The application checks at regular intervals the availability of services on the '
                       'specified ip address (or hostname) and port',
        'version': '1.0.0',
        'uiversion': 3,
        'termsOfService': '',
        # 'specs_route': '/apidocs/'

    }
    # Celery Config
    CELERY = {
        'broker_url': os.environ.get("CELERY_BROKER_URL"),
        'result_backend': os.environ.get("CELERY_RESULT_BACKEND_URL"),
        'redbeat_redis_url': os.environ.get('CELERY_REDBEAT_REDIS_URL'),
        'beat_scheduler': 'redbeat.RedBeatScheduler',
        'redbeat_key_prefix': 'redbeat:',
        'beat_max_loop_interval': 5,
        'beat_schedule': {
            # Execute every 30sec (by default) after enabled by user
            'watchdog-task': {
                'task': 'watchdog_task',
                'schedule': schedules.schedule(run_every=30),
                'relative': True,
                'enabled': False
            },
            # Execute every 20sec
            'background-task': {
                'task': 'service_unknown_status_task',
                'schedule': 20.0,
                'relative': True,
                'enabled': True
            }
        }
    }


class ProdConfig(Config):
    """
    Set Flask configuration vars for production.
    """
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_URI_PROD'),
    }


class TestConfig(Config):
    """
    Set Flask configuration vars for testing.
    """
    DEBUG = True
    TESTING = True
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_URI_TEST', 'mongodb://localhost:27017/testdb'),
    }


class DevConfig(Config):
    """
    Set Flask configuration vars for testing.
    """
    DEBUG = True
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGODB_URI_DEV', 'mongodb://localhost:27017/devdb'),
    }


app_config = {
    'development': DevConfig,
    'testing': TestConfig,
    'production': ProdConfig,
}