import logging

from pymongo import MongoClient, errors
from pymongo.uri_parser import parse_uri
from flask import current_app
from redis.exceptions import ConnectionError as RedisConnectionError

from api_service.watchdog_celery.monitoring import MonitoringService
from api_service.extensions import celery
from api_service.watchdog_celery.monitoring import WatchdogEntry


@celery.task(name='watchdog_task')
def watchdog_task():
    """
    Run watchdog (monitoring) service.
    """
    # Logging configuration
    log_format = '%(asctime)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)

    mongodb_uri = current_app.config.get('MONGODB_SETTINGS')['host']
    # Get database name directly from the MongoDB URI.
    # When you use MongoClient with 'host' parameter, the database name in URI is being ignored.
    mongodb_db_name = parse_uri(mongodb_uri)['database']

    with MongoClient(host=mongodb_uri, serverSelectionTimeoutMS=10000) as client:
        # MongoDB connection timeout is set to 10 sec
        # Use database from MongoDB URI
        db = client[mongodb_db_name]
        watchdog = MonitoringService(db)
        try:
            watchdog.start()
        except errors.ServerSelectionTimeoutError:
            logging.error(f'MongoDB server is not reachable')


@celery.task(name='service_status_task')
def service_status_task():
    """
    Changing services status if watchdog is down.
    The task is executed as a background job (triggered at regular intervals).
    """
    # TODO: changing services status if watchdog is down
    try:
        watchdog_job = WatchdogEntry()
        print(f'Watchdog enabled: {watchdog_job.enabled}')
    except (KeyError, RedisConnectionError):
        print(f'Watchdog enabled: False')