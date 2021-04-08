import sys
import subprocess
from datetime import datetime
import socket
import logging
import threading
from uuid import uuid4


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
        # while True:
        #     timer_start = time.perf_counter()
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
            # time_interval = time.perf_counter() - timer_start
            # if time_interval > self.timer:
            #     continue
            # time.sleep(self.timer - time_interval)

    def check_service_status(self, service):
        """
        Checks the status of a particular service.
        """
        host_type = service['host']['type']
        host_value = service['host']['value']
        port = service['port']
        service_name = service['name']
        # Get mongodb id ('_id') of current service
        service_id = service['_id']
        # Service will be updated using MongoDB id ('_id')
        service_to_update = {'_id': service_id}
        logging.info(f'Started checking the "{service_name}" service')

        # Check host type and resolve hostname to ip if needed.
        if host_type == 'hostname':
            host_value = self.resolve_hostname(host_value)
            if not host_value:
                # Change 'service_up' status if 'True'
                if service['service_up']:
                    # Update service status to 'False' (update db document)
                    self.service_collection.update_one(service_to_update, {'$set': {'service_up': False}})
                # Close thread if problem with resolving occurred.
                sys.exit()
        if service['proto'] == 'tcp':
            # Set timeout 1s (w 1)
            response = subprocess.run(['nc', '-z', '-w 2', host_value, port], capture_output=True)
        else:
            response = subprocess.run(['nc', '-zu', host_value, port], capture_output=True)
        if response.returncode == 0:
            # Mark service as responded
            response_time_update = {'$set': {'timestamps.last_responded': datetime.utcnow()}}
            self.service_collection.update_one(service_to_update, response_time_update)
            service_status = True
        else:
            service_status = False
        # Mark service as tested
        tested_time_update = {'$set': {'timestamps.last_tested': datetime.utcnow()}}
        self.service_collection.update_one(service_to_update, tested_time_update)

        # Update service in db only if 'status' is changed
        if service_status != service['service_up']:
            status_new_value = {'$set': {'service_up': service_status}}
            # Update service status (update db document)
            self.service_collection.update_one(service_to_update, status_new_value)
            logging.info(f'The "{service_name}" changed status to {"UP" if service_status else "DOWN"}')
        logging.info(f'The "{service_name}" service is {"UP" if service_status else "DOWN"}')

    @staticmethod
    def resolve_hostname(hostname):
        """
        Performs DNS query if host is not an ip address.
        """
        try:
            ip = socket.gethostbyname(hostname)
            return ip
        except socket.gaierror as err:
            logging.error(f'{hostname}: {err.strerror}')
            return False