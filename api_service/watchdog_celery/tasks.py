from pymongo import MongoClient, errors
from pymongo.uri_parser import parse_uri
from flask import current_app
from redis.exceptions import ConnectionError as RedisConnectionError

from api_service.watchdog_celery.monitoring import MonitoringService
from api_service.extensions import celery
from api_service.watchdog_celery.monitoring import WatchdogEntry


def get_mongo_db_name():
    """
    Get database name directly from the MongoDB URI.
    """
    mongodb_uri = current_app.config.get('MONGODB_SETTINGS')['host']
    # When you use MongoClient with 'host' parameter, the database name in URI is being ignored.
    mongodb_db_name = parse_uri(mongodb_uri)['database']
    return mongodb_uri, mongodb_db_name


@celery.task(name='watchdog_task')
def watchdog_task():
    """
    Run watchdog (monitoring) service.
    """
    mongodb_uri, mongodb_db_name = get_mongo_db_name()
    with MongoClient(host=mongodb_uri, serverSelectionTimeoutMS=10000) as client:
        # MongoDB connection timeout is set to 10 sec
        # Use database from MongoDB URI
        db = client[mongodb_db_name]
        watchdog = MonitoringService(db)
        try:
            watchdog.start()
        except errors.ServerSelectionTimeoutError:
            current_app.logger.error('MongoDB server is not reachable')


@celery.task(name='service_unknown_status_task')
def change_status_to_unknown_task():
    """
    Changing services status if watchdog is down.
    The task is executed as a background job (triggered at regular intervals).
    """
    try:
        watchdog_job = WatchdogEntry()
        print(f'Watchdog enabled: {watchdog_job.enabled}')
    except (KeyError, RedisConnectionError) as error:
        current_app.logger.error(f'Error: {error} in service_status_task')
        return

    if not watchdog_job.enabled:
        mongodb_uri, mongodb_db_name = get_mongo_db_name()
        with MongoClient(host=mongodb_uri, serverSelectionTimeoutMS=10000) as client:
            db = client[mongodb_db_name]

            services = db.service.find()

            for service in services:
                # Break loop if watchdog service is started during iteration execution.
                if not watchdog_job.enabled:
                    break
                if service['status'] != 'unknown':
                    # db.service.update_one({'_id': service['_id']}, {'$set': {'status': 'unknown'}})
                    pass
                print(f'{service["name"]}')