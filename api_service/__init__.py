from flask import Flask

from config import Config
from api_service.extensions import api, db, swag
from api_service.services import views as serv_views


def create_app():
    """
    Construct the core app object.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    with app.app_context():
        # Initialize Plugins
        register_extensions(app)
        register_blueprints(app)
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
