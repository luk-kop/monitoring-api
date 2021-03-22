#!/usr/bin/python3
import os
import subprocess
from datetime import datetime
import time
import socket
import logging
from pymongo import MongoClient, errors
import threading
from uuid import uuid4

from dotenv import load_dotenv


class MonitoringService:

    def __init__(self, db, timer=10):
        self.timer = timer
        self.db = db
        # Service collection
        self.service_collection = self.db.service

    def start(self):
        """
        Starts a watchdog service. Each service is being tested in a separate thread.
        """
        while True:
            timer_start = time.perf_counter()
            services = self.service_collection.find()
            # Checks if there are any documents in the collection
            if self.service_collection.count_documents({}):
                for service in services:
                    # Check status of each service in separate thread.
                    status_thread = threading.Thread(target=self.check_service_status,
                                                     args=[service],
                                                     daemon=True,
                                                     name=f'service-{uuid4().hex}')
                    status_thread.start()
            else:
                logging.info('No service documents in the db')
            time_interval = time.perf_counter() - timer_start
            if time_interval > self.timer:
                continue
            time.sleep(self.timer - time_interval)
            # print([thread.name for thread in threading.enumerate()])      # TODO" to delete

    def check_service_status(self, service):
        """
        Checks the status of a particular service.
        """
        # TODO: check ip and continue if exception
        host = service['host']
        port = service['port']
        service_name = service['name']
        # Get mongodb id ('_id') of current service
        service_id = service['_id']
        # Service will be updated using mongodb id ('_id')
        service_to_update = {'_id': service_id}
        logging.info(f'Started checking the "{service_name}" service')
        if service['proto'] == 'tcp':
            # Set timeout 1s (w 1)
            response = subprocess.run(['nc', '-z', '-w 1', host, port], capture_output=True)
        else:
            response = subprocess.run(['nc', '-zu', host, port], capture_output=True)
        if response.returncode == 0:
            # Mark service as responded
            response_new_value = {'$set': {'last_responded': datetime.utcnow()}}
            self.service_collection.update_one(service_to_update, response_new_value)
            service['last_responded'] = datetime.utcnow()
            service_status = True
        else:
            service_status = False
        # Update service in db only if 'status' is changed
        if service_status != service['service_up']:
            status_new_value = {'$set': {'service_up': service_status}}
            # print(self.service_collection.find_one(service_to_update))  # TODO: to delete
            # Update service status (update db document)
            self.service_collection.update_one(service_to_update, status_new_value)
            # print(self.service_collection.find_one(service_to_update))  # TODO: to delete
            logging.info(f'The "{service_name}" changed status to {"UP" if service_status else "DOWN"}')
        logging.info(f'The "{service_name}" service is {"UP" if service_status else "DOWN"}')

    @staticmethod
    def check_ip(host):
        """
        Performs DNS query if host is not an ip address.
        """
        try:
            ip = socket.gethostbyname(host)
            print(f'Hostname: {host}, IP: {ip}')            # TODO: to delete
            return ip
        except socket.gaierror as err:
            logging.error(f'{host}: {err.strerror}')
            return False


if __name__ == "__main__":
    # Logging configuration
    log_format = '%(asctime)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.DEBUG)

    # Load environment vars
    load_dotenv('.env-watchdog')
    mongodb_url = os.getenv("MONGODB_URL")

    with MongoClient(mongodb_url) as client:
        # Use 'watchdogdb' database
        db = client.watchdogdb
        watchdog = MonitoringService(db)
        try:
            watchdog.start()
        except errors.ServerSelectionTimeoutError:
            logging.error(f'MongoDB server is not reachable')
            # TODO: some exception to exit script, container will be restarted by orchestrator

