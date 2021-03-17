#!/usr/bin/python3
import os
from datetime import datetime
import time
from pymongo import MongoClient


class MonitoringService:

    def __init__(self, db, timer=10):
        self.timer = timer
        self.db = db
        # Services collection
        self.services_collection = self.db.services

    def start(self):
        while True:
            timer_start = time.perf_counter()
            services = self.get_services()
            if services:
                for service in services:
                    ip = service['ip']
                    port = service['port']
                    service_to_update = {'name': service['name']}                       # TODO: validate unique service name
                    if service['proto'] == 'tcp':
                        # timeout 1s (w 1)
                        response = os.system(f'nc -z -w 1 {ip} {port}')
                    else:
                        response = os.system(f'nc -zu {ip} {port}')
                    if response == 0:
                        print(f'{service["name"]} is UP!')
                        # Mark service as responded
                        response_new_value = {'$set': {'last_responded': datetime.utcnow()}}
                        self.services_collection.update_one(service_to_update, response_new_value)
                        service['last_responded'] = datetime.utcnow()
                        service_status = True
                    else:
                        print(f'{service["name"]} is DOWN')
                        service_status = False
                    # Update service in db only if 'status' is changed
                    if service_status != service['service_up']:
                        status_new_value = {'$set': {'service_up': service_status}}
                        print(self.services_collection.find_one(service_to_update))        # TODO: to delete
                        # Update service status
                        self.services_collection.update_one(service_to_update, status_new_value)
                        print(self.services_collection.find_one(service_to_update))        # TODO: to delete
            time_interval = time.perf_counter() - timer_start
            print(time_interval)
            if time_interval > self.timer:
                continue
            time.sleep(self.timer - time_interval)

    def get_services(self):
        """
        Fetch all services from db.
        """
        return self.services_collection.find()

    def update_service(self, service):
        pass


if __name__ == "__main__":
    with MongoClient('mongodb://localhost:27017') as client:
        # Use 'watchdogdb' database
        db = client.watchdogdb
        watchdog = MonitoringService(db)
        watchdog.start()

