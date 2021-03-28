from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os


services_dummy_data = [
    {
        'name': 'dns-service',
        'host': {
            'type': 'ip',
            'value': '1.1.1.1'
        },
        'port': '53',
        'proto': 'udp',
        'timestamps': {
            'last_responded': None,
            'last_tested': None,
            'created': datetime.utcnow(),
            'edited': datetime.utcnow()
        },
        'service_up': True
    },
    {
        'name': 'wrong-hostname',
        'host': {
            'type': 'hostname',
            'value': 'xxx.local.sdsdsd'
        },
        'port': '123',
        'proto': 'udp',
        'timestamps': {
            'last_responded': None,
            'last_tested': None,
            'created': datetime.utcnow(),
            'edited': datetime.utcnow()
        },
        'service_up': True
    },
    {
        'name': 'home-ssh-service',
        'host': {
            'type': 'ip',
            'value': '192.168.1.1'
        },
        'port': '22',
        'proto': 'tcp',
        'timestamps': {
            'last_responded': None,
            'last_tested': None,
            'created': datetime.utcnow(),
            'edited': datetime.utcnow()
        },
        'service_up': True
    },
    {
        'name': 'home-ntp-service',
        'host': {
            'type': 'ip',
            'value': '192.168.1.1'
        },
        'port': '123',
        'proto': 'tcp',
        'timestamps': {
            'last_responded': None,
            'last_tested': None,
            'created': datetime.utcnow(),
            'edited': datetime.utcnow()
        },
        'service_up': True
    },
    {
        'name': 'localhost-nmea-service',
        'host': {
            'type': 'ip',
            'value': '172.16.1.126'
        },
        'port': '10110',
        'proto': 'tcp',
        'timestamps': {
            'last_responded': None,
            'last_tested': None,
            'created': datetime.utcnow(),
            'edited': datetime.utcnow()
        },
        'service_up': True
    },
    {
        'name': 'dns-google',
        'host': {
            'type': 'hostname',
            'value': 'google-public-dns-b.google.com'
        },
        'port': '53',
        'proto': 'tcp',
        'timestamps': {
            'last_responded': None,
            'last_tested': None,
            'created': datetime.utcnow(),
            'edited': datetime.utcnow()
        },
        'service_up': True
    }
]

# Load environment vars
load_dotenv('.env-watchdog')
mongodb_url = os.getenv("MONGODB_URL")

with MongoClient(mongodb_url) as client:
    # Use 'watchdogdb' db
    db = client.watchdogdb
    service = db.service
    # Drop collection if exists
    service.drop()
    service.insert_many(services_dummy_data)
