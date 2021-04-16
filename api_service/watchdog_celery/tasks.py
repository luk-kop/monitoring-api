import os
import logging

from pymongo import MongoClient, errors
from celery import Celery, schedules
from redbeat import RedBeatSchedulerEntry

from config import ConfigCelery
from api_service.watchdog_celery.monitoring import MonitoringService


celery_app = Celery(__name__)
celery_app.config_from_object(ConfigCelery)
# Create scheduler - default interval 20s
interval = schedules.schedule(run_every=20)
scheduler_job = RedBeatSchedulerEntry(name='background-task',
                                      task='watchdog_task',
                                      schedule=interval,
                                      relative=True,
                                      enabled=False,
                                      app=celery_app)
scheduler_job.save()


@celery_app.task(name='watchdog_task')
def watchdog_task():
    # Logging configuration
    log_format = '%(asctime)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)

    mongodb_url = os.getenv("MONGODB_URL")

    with MongoClient(host=mongodb_url, serverSelectionTimeoutMS=10000) as client:
        # MongoDB connection timeout is set to 10s
        # Use 'watchdogdb' database
        db = client.watchdogdb
        watchdog = MonitoringService(db)
        try:
            watchdog.start()
        except errors.ServerSelectionTimeoutError:
            logging.error(f'MongoDB server is not reachable')