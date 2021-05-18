import os

from pytest import fixture
from pymongo.uri_parser import parse_uri
from mongoengine import connect, disconnect

from api_service import create_app
from api_service.extensions import db
from api_service.models import Service


def get_db_name():
    """
    Get test database name from MongoDB URI.
    """
    mongo_uri = os.environ.get('MONGODB_URI_TEST', 'mongodb://localhost:27017/testdb')
    return parse_uri(mongo_uri)['database']


@fixture(scope='module')
def test_client():
    flask_app = create_app(config_mode='testing')
    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            # Testing happens here
            yield testing_client
            # Delete test db after tests completion
            db_name = get_db_name()
            db.connection.drop_database(name_or_database=db_name)
        # Disconnect from MongoDB
        disconnect()


@fixture(scope='module')
def add_two_services(test_client):
    services_data = [
        {
            'name': 'test-service-telnet-03',
            'host': {
                'type': 'hostname',
                'value': 'test123.service.local'
            },
            'proto': 'tcp',
            'port': '23'
        },
        {
            'name': 'test-service-ssh',
            'host': {
                'type': 'ip',
                'value': '192.168.1.11'
            },
            'proto': 'tcp',
            'port': '22'
        }
    ]
    for service in services_data:
        Service(**service).save()


@fixture(scope='module')
def add_four_services(test_client):
    services_data = [
        {
            'name': 'test-google-dns-01',
            'host': {
                'type': 'ip',
                'value': '8.8.8.8'
            },
            'proto': 'udp',
            'port': '53'
        },
        {
            'name': 'test-google.com',
            'host': {
                'type': 'hostname',
                'value': 'www.google.com'
            },
            'proto': 'tcp',
            'port': '443'
        },
        {
            'name': 'test-fake-service-01',
            'host': {
                'type': 'ip',
                'value': '192.168.1.1'
            },
            'proto': 'tcp',
            'port': '1234'
        },
        {
            'name': 'test-fake-service-02',
            'host': {
                'type': 'ip',
                'value': '192.168.1.2'
            },
            'proto': 'udp',
            'port': '1234'
        }
    ]
    for service in services_data:
        Service(**service).save()


@fixture
def example_service_data():
    service = {
        'name': 'test-service-dns-02',
        'host': {
            'type': 'hostname',
            'value': 'test.service.local'
        },
        'proto': 'udp',
        'port': '53'
    }
    return service


@fixture(scope='module')
def init_database():
    db_name = get_db_name()
    db_connection = connect(db_name)
    yield
    db_connection.drop_database(db_name)


