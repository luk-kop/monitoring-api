from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
from uuid import uuid4


services_dummy_data = [
    {
        'id': str(uuid4()),
        'name': 'dns-service',
        'host': '1.1.1.1',
        'port': '53',
        'proto': 'udp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    },
    {
        'id': str(uuid4()),
        'name': 'home-ssh-service',
        'host': '192.168.1.1',
        'port': '22',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    },
    {
        'id': str(uuid4()),
        'name': 'home-ntp-service',
        'host': '192.168.1.1',
        'port': '123',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    },
    {
        'id': str(uuid4()),
        'name': 'localhost-nmea-service',
        'host': '172.16.1.126',
        'port': '10110',
        'proto': 'tcp',
        'last_responded': None,
        'last_configured': datetime.utcnow().isoformat(),
        'service_up': True
    }
]

# Load environment vars
load_dotenv('.env-watchdog')
mongodb_url = os.getenv("MONGODB_URL")

with MongoClient(mongodb_url) as client:
    # Use 'watchdogdb' db
    db = client.watchdogdb
    services = db.services
    # Drop collection if exists
    services.drop()
    services.insert_many(services_dummy_data)
