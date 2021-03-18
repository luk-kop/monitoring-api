from pymongo import MongoClient
from datetime import datetime


services_dummy_data = [
    {
        'name': 'dns-service',
        'host': '1.1.1.1',
        'port': '53',
        'proto': 'udp',
        'last_responded': None,
        'last_configured': datetime.utcnow(),
        'service_up': True
    },
    {
        'name': 'home-ssh-service',
        'host': '192.168.1.1',
        'port': '22',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow(),
        'service_up': True
    },
    {
        'name': 'home-ntp-service',
        'host': '192.168.1.1',
        'port': '123',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow(),
        'service_up': True
    },
    {
        'name': 'localhost-nmea-service',
        'host': '127.0.0.1',
        'port': '10110',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow(),
        'service_up': True
    }
]

with MongoClient('mongodb://localhost:27017') as client:
    # Use 'watchdogdb' db
    db = client.watchdogdb
    services = db.services
    # Drop collection if exists
    services.drop()
    services.insert_many(services_dummy_data)
