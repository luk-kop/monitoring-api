import os
import logging
import sys

from flask import Flask

from config import app_config
from api_service.extensions import api, db, swag, celery
from api_service.services import views as serv_views


def create_app(config_mode=os.environ.get('APP_MODE')):
    """
    Construct the core app object.
    """
    app = Flask(__name__)
    app.config.from_object(app_config[config_mode])
    with app.app_context():
        # Initialize Plugins
        register_extensions(app)
        register_blueprints(app)
        init_celery(app)
        configure_logger(app)
        return app


def register_extensions(app):
    """
    Register Flask extensions.
    """
    api.add_resource(serv_views.ServicesApi, '/services')
    api.add_resource(serv_views.ServiceApi, '/services/<string:service_id>')
    api.add_resource(serv_views.WatchdogApi, '/watchdog')
    api.init_app(app)
    db.init_app(app)
    swag.init_app(app)


def register_blueprints(app):
    """
    Register Flask blueprints.
    """
    app.register_blueprint(serv_views.serv_bp)


def init_celery(app=None):
    """
    Initialize celery.
    """
    app = app or create_app(os.environ.get('APP_MODE'))
    celery.conf.update(app.config.get("CELERY", {}))

    class ContextTask(celery.Task):
        """
        Make celery tasks work with Flask app context
        """
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def configure_logger(app):
    """
    Configure loggers.
    """
    app_formatter = logging.Formatter('%(asctime)s: %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(app_formatter)
    handler.setLevel(logging.DEBUG)
    if not app.logger.handlers:
        app.logger.addHandler(handler)