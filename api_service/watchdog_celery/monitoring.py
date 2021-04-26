import sys
import subprocess
from datetime import datetime
import socket
import logging
import threading
from uuid import uuid4

from redbeat import RedBeatSchedulerEntry

from api_service.extensions import celery


class MonitoringService:
    """
    Class specifying the object responsible for checking the status of monitored services.
    """
    def __init__(self, db, timer=10):
        self.timer = timer
        self.db = db
        # Service collection
        self.service_collection = self.db.service

    def start(self):
        """
        Starts a watchdog service. Each service is being tested in a separate thread.
        """
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

    def check_service_status(self, service: dict):
        """
        Checks the status of a particular service.
        """
        host_type, host_value = service['host']['type'], service['host']['value']
        service_port, service_protocol = service['port'], service['proto']
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
        # Check port status
        response = self.port_status(service_protocol, host_value, service_port)
        if response:
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
    def resolve_hostname(hostname: str) -> str:
        """
        Performs DNS query if host is not an ip address.
        """
        try:
            ip = socket.gethostbyname(hostname)
            return ip
        except socket.gaierror as err:
            logging.error(f'{hostname}: {err.strerror}')
            return ''

    @staticmethod
    def port_status(proto: str, ip_address: str, port: str) -> str:
        """
        Check whether host is listening on specified port.
        """
        if proto == 'tcp':
            options = ['nc', '-z', '-w 2', ip_address, port]
            response = subprocess.run(args=options, capture_output=True, text=True)
            return True if response.returncode == 0 else False
        else:
            options = ['sudo', 'nmap', '-sU', '-p', port, '-oG', '-', ip_address]
            response = subprocess.run(args=options, capture_output=True, text=True)
            return True if f'{port}/open' in response.stdout else False


class WatchdogEntry:
    """
    Proxy to celery job.
    """
    def __init__(self, key='redbeat:watchdog-task'):
        self.key = key
        # Return KeyError or RedisConnectionError if encounter problem with Redis
        self.job = RedBeatSchedulerEntry.from_key(key=self.key, app=celery)

    @property
    def enabled(self):
        return self.job.enabled

    def enable_job(self):
        self.job.enabled = True
        self.job.save()

    def disable_job(self):
        self.job.enabled = False
        self.job.save()
