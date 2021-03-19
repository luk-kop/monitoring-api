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
        # Services collection
        self.services_collection = self.db.services

    def start(self):
        """
        Starts a watchdog service. Each service is being tested in a separate thread.
        """
        while True:
            timer_start = time.perf_counter()
            services = self.get_services()
            if services:
                for service in services:
                    # Check status of each service in separate thread.
                    status_thread = threading.Thread(target=self.check_service_status,
                                                     args=[service],
                                                     daemon=True,
                                                     name=f'service-{uuid4().hex}')
                    status_thread.start()
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
        service_to_update = {'name': service_name}  # TODO: validate unique service name
        logging.info(f'Started checking the "{service_name}" service')
        if service['proto'] == 'tcp':
            # Set timeout 1s (w 1)
            response = subprocess.run(['nc', '-z', '-w 1', host, port], capture_output=True)
        else:
            response = subprocess.run(['nc', '-zu', host, port], capture_output=True)
        if response.returncode == 0:
            # Mark service as responded
            response_new_value = {'$set': {'last_responded': datetime.utcnow()}}
            self.services_collection.update_one(service_to_update, response_new_value)
            service['last_responded'] = datetime.utcnow()
            service_status = True
        else:
            service_status = False
        # Update service in db only if 'status' is changed
        if service_status != service['service_up']:
            status_new_value = {'$set': {'service_up': service_status}}
            # print(self.services_collection.find_one(service_to_update))  # TODO: to delete
            # Update service status (update db document)
            self.services_collection.update_one(service_to_update, status_new_value)
            # print(self.services_collection.find_one(service_to_update))  # TODO: to delete
            logging.info(f'The "{service_name}" changed status to {"UP" if service_status else "DOWN"}')
        logging.info(f'The "{service_name}" service is {"UP" if service_status else "DOWN"}')

    def get_services(self):
        """
        Fetch all services from db.
        """
        return self.services_collection.find()

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
    MONGODB_URL = os.getenv("MONGODB_URL")

    with MongoClient(MONGODB_URL) as client:
        # Use 'watchdogdb' database
        db = client.watchdogdb
        watchdog = MonitoringService(db)
        try:
            watchdog.start()
        except errors.ServerSelectionTimeoutError:
            logging.error(f'MongoDB server is not reachable')
            # TODO: some exception to exit script, container will be restarted by orchestrator

