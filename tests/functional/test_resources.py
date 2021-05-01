import json
from bson import objectid


def test_get_services_endpoint_empty(test_client):
    """
    GIVEN Flask application configured for testing
    WHEN the '/services' endpoint is requested (GET)
    THEN check that there are any documents in db
    """
    response = test_client.get('/services')
    json_data = response.get_json()
    assert response.status_code == 200
    assert 'data' in json_data
    assert 'paging' in json_data
    assert json_data['data']['services'] == []


def test_get_endpoints(test_client):
    """
    GIVEN Flask application configured for testing
    WHEN the one of available endpoints is requested (GET)
    THEN check correct code is returned
    """
    endpoints_to_test = {
        '/': 404,
        '/services': 200,
        f'/services/{objectid.ObjectId()}': 404,
        '/watchdog': 200
    }
    for endpoint, status_code in endpoints_to_test.items():
        response = test_client.get(endpoint)
        assert response.status_code == status_code


def test_create_service(test_client, example_service_data):
    """
    GIVEN Flask application configured for testing
    WHEN the '/services' endpoint is posted (POST)
    THEN check that a '201' code is returned
    """
    headers = {
        "Content-Type": "application/json",
    }
    response = test_client.post('/services', headers=headers, data=json.dumps(example_service_data))
    assert response.status_code == 201


def test_count_services(test_client):
    """
    GIVEN Flask application configured for testing
    WHEN the '/services' page is requested (GET)
    THEN check that one document in db
    """
    response = test_client.get('/services')
    json_data = response.get_json()
    assert len(json_data['data']['services']) == 1


def test_create_service_bad_request(test_client, example_service_data):
    """
    GIVEN Flask application configured for testing and dummy service data
    WHEN the '/services' page is requested (GET)
    THEN check that a '400' code is returned
    """
    post_data = example_service_data
    headers = {
        "Content-Type": "application/json",
    }
    response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
    # Service already exists
    assert response.status_code == 400
    post_data['name'] = 'web-service123'
    # Wrong host type
    post_data['host']['type'] = 'test'
    response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
    assert response.status_code == 400
    # Wrong 'value' for 'type' = 'ip'
    post_data['host']['type'] = 'ip'
    for ip_value in ['test', '111.1111.1', 123, '300.168.1.1', 'wp.pl']:
        post_data['host']['value'] = ip_value
        response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
        assert response.status_code == 400
    # Wrong 'value' for 'type' = 'hostname'
    post_data['host']['type'] = 'hostname'
    for host_value in ['test@', '#test', 123]:
        post_data['host']['value'] = host_value
        response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
        assert response.status_code == 400
    # Wrong protocol
    post_data['host']['value'] = 'test.example.com'
    for proto in ['smtp', 123, 'http']:
        post_data['proto'] = proto
        response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
        assert response.status_code == 400
    # Wrong port
    post_data['proto'] = 'tcp'
    for port in [0, 'smtp', 123, 'http', '66666']:
        post_data['port'] = port
        response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
        assert response.status_code == 400


def test_create_and_delete_service(test_client, example_service_data):
    """
    GIVEN Flask application configured for testing
    WHEN service added to db is deleted with '/services/{service_id}' (DELETE) request
    THEN check that a '201' code is returned (when added) and '200' (when deleted)
    """
    post_data = example_service_data
    post_data['name'] = 'service-to-delete-001'
    headers = {
        "Content-Type": "application/json",
    }
    response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
    assert response.status_code == 201
    # Delete added service
    service_id = response.get_json()['id']
    response = test_client.delete(f'/services/{service_id}')
    assert response.status_code == 200


def test_delete_service_not_exist(test_client):
    """
    GIVEN Flask application configured for testing and random generated service id
    WHEN the '/services/{service_id}' endpoint is requested (DELETE)
    THEN check that a '404' code is returned
    """
    # Generate random service id
    service_id = objectid.ObjectId()
    response = test_client.delete(f'/services/{service_id}')
    json_data = response.get_json()
    assert response.status_code == 404
    assert json_data['message'] == f'Service with id {service_id} does not exist.'


def test_count_services_after_added(test_client, add_services):
    """
    GIVEN Flask application configured for testing and additional services in db
    WHEN the '/services' endpoint is requested (GET)
    THEN check that a '200' code is returned and number of returned services in db
    """
    response = test_client.get('/services')
    json_data = response.get_json()
    assert response.status_code == 200
    assert len(json_data['data']['services']) == 3


def test_delete_one_service_and_decreased_services_count(test_client):
    """
    GIVEN Flask application configured for testing and services in db
    WHEN new service is deleted
    THEN service with specified id is deleted and total services count is decreased by one
    """
    response = test_client.get('/services')
    json_data = response.get_json()
    assert response.status_code == 200
    # Get services count
    services_total = json_data['data']['services_total']
    assert services_total != 0
    # Get service id (1st service)
    service_id = json_data['data']['services'][0]['id']
    # Delete service
    response = test_client.delete(f'/services/{service_id}')
    assert response.status_code == 200
    # Confirm total services count decreased by one
    response = test_client.get('/services')
    json_data = response.get_json()
    assert json_data['data']['services_total'] == services_total - 1


def test_put_service_not_exist(test_client):
    """
    GIVEN Flask application configured for testing and random generated service id
    WHEN the '/services/{service_id}' endpoint is requested (PUT)
    THEN check that a '404' code is returned
    """
    # Generate random service id
    service_id = objectid.ObjectId()
    response = test_client.put(f'/services/{service_id}')
    json_data = response.get_json()
    assert response.status_code == 404
    assert json_data['message'] == f'Service with id {service_id} does not exist.'


def test_put_service(test_client, example_service_data):
    """
    GIVEN Flask application configured for testing and service to update
    WHEN the '/services/{service_id}' endpoint is requested (PUT)
    THEN check that service exist and can be updated
    """
    response = test_client.get('/services')
    json_data = response.get_json()
    assert response.status_code == 200
    # Get service id (1st service)
    service_id = json_data['data']['services'][0]['id']
    # Update service
    put_data = example_service_data
    put_data['name'] = 'service-updated-001'
    put_data['host']['type'] = 'ip'
    put_data['host']['value'] = '192.168.1.11'
    put_data['proto'] = 'udp'
    put_data['port'] = '555'
    headers = {
        "Content-Type": "application/json",
    }
    response = test_client.put(f'/services/{service_id}', headers=headers, data=json.dumps(put_data))
    assert response.status_code == 200


def test_put_service_updated(test_client):
    """
    GIVEN Flask application configured for testing with updated service
    WHEN the '/services' endpoint is requested (GET)
    THEN check that service is updated correctly
    """
    response = test_client.get('/services')
    json_data = response.get_json()
    assert response.status_code == 200
    # Get updated service (with PUT)
    service = [service for service in json_data['data']['services'] if service['name'] == 'service-updated-001']
    assert len(service) == 1
    service = service[0]
    assert service['host']['type'] == 'ip'
    assert service['host']['value'] == '192.168.1.11'
    assert service['proto'] == 'udp'
    assert service['port'] == '555'


def test_patch_service_bad_request(test_client):
    """
    GIVEN Flask application configured for testing and service to update
    WHEN the '/services/{service_id}' endpoint is requested (PATCH) with wrong data
    THEN check that a '400' code is returned
    """
    headers = {
        "Content-Type": "application/json",
    }
    response = test_client.get('/services')
    json_data = response.get_json()
    assert response.status_code == 200
    # Get service for a test
    service_id  = json_data['data']['services'][0]['id']
    # Service name already exists
    path_data = {'name': 'test-service-ssh'}
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
    assert response.status_code == 400
    # Wrong host type
    path_data = {
        'host': {
            'type': 'test',
            'value': '123.123.123.123'
        }
    }
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
    assert response.status_code == 400
    # Only type
    for host_type in ['hostname', 'ip']:
        path_data = {
            'host': {
                'type': host_type
            }
        }
        response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
        assert response.status_code == 400
    # Only value
    for host_value in ['test01.example.com', '192.168.1.1']:
        path_data = {
            'host': {
                'value': host_value
            }
        }
        response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
        assert response.status_code == 400
    # Wrong 'value' for 'type' = 'ip'
    path_data = {
        'host': {
            'type': 'ip',
            'value': ''
        }
    }
    for ip_value in ['test', '111.1111.1', 123, '300.168.1.1', 'wp.pl']:
        path_data['host']['value'] = ip_value
        response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
        assert response.status_code == 400
    # Wrong 'value' for 'type' = 'hostname'
    path_data = {
        'host': {
            'type': 'hostname',
            'value': ''
        }
    }
    for host_value in ['test@', '#test', 123]:
        path_data['host']['value'] = host_value
        response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
        assert response.status_code == 400
    # Wrong protocol
    path_data = {'proto': ''}
    for proto in ['smtp', 123, 'http']:
        path_data['proto'] = proto
        response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
        assert response.status_code == 400
    # Wrong port
    path_data = {'port': ''}
    for port in [0, 'smtp', 123, 'http', '66666']:
        path_data['port'] = port
        response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(path_data))
        assert response.status_code == 400


def test_patch_service(test_client):
    """
    GIVEN Flask application configured for testing and service to update
    WHEN the '/services/{service_id}' endpoint is requested (PATCH)
    THEN check that service exist and can be updated
    """
    headers = {
        "Content-Type": "application/json",
    }
    response = test_client.get('/services')
    json_data = response.get_json()
    # Get service id for a test
    service_id = json_data['data']['services'][0]['id']
    # Update service name
    patch_data = {'name': 'service-patched-001'}
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(patch_data))
    assert response.status_code == 200
    # Update host data (ip)
    patch_data = {
        'host': {
            'type': 'ip',
            'value': '192.168.1.12'
        }
    }
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(patch_data))
    assert response.status_code == 200
    # Update host data (hostname)
    patch_data = {
        'host': {
            'type': 'hostname',
            'value': 'test01.example.com'
        }
    }
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(patch_data))
    assert response.status_code == 200
    # Update protocol (TCP)
    patch_data = {
        'proto': 'tcp'
    }
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(patch_data))
    assert response.status_code == 200
    # Update protocol (UDP)
    patch_data = {
        'proto': 'udp'
    }
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(patch_data))
    assert response.status_code == 200
    # Update network port
    patch_data = {
        'port': '123'
    }
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(patch_data))
    assert response.status_code == 200
    # All updates in one request
    patch_data = {
        'name': 'service-patched-002',
        'host': {
            'type': 'ip',
            'value': '10.10.10.10'
        },
        'proto': 'tcp',
        'port': '321'
    }
    response = test_client.patch(f'/services/{service_id}', headers=headers, data=json.dumps(patch_data))
    assert response.status_code == 200


def test_patch_service_updated(test_client):
    """
    GIVEN Flask application configured for testing with updated service
    WHEN the '/services' endpoint is requested (GET)
    THEN check that service is updated correctly
    """
    response = test_client.get('/services')
    json_data = response.get_json()
    assert response.status_code == 200
    # Get updated service (with PUT)
    service = [service for service in json_data['data']['services'] if service['name'] == 'service-patched-002']
    assert len(service) == 1
    service = service[0]
    assert service['host']['type'] == 'ip'
    assert service['host']['value'] == '10.10.10.10'
    assert service['proto'] == 'tcp'
    assert service['port'] == '321'


def test_watchdog_not_running(test_client):
    """
    GIVEN Flask application configured for testing and watchdog service is not running
    WHEN the '/watchdog' endpoint is requested (GET)
    THEN watchdog service is down
    """
    response = test_client.get('/watchdog')
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data['watchdog_status'] == 'down'


def test_watchdog_start(test_client):
    """
    GIVEN Flask application configured for testing and watchdog service is stopped
    WHEN the '/watchdog' endpoint is requested (POST) with 'start' option
    THEN watchdog service is up
    """
    headers = {
        "Content-Type": "application/json",
    }
    post_data = {
        'watchdog': 'start'
    }
    response = test_client.post('/watchdog', headers=headers, data=json.dumps(post_data))
    assert response.status_code == 201


def test_watchdog_start_when_running(test_client):
    """
    GIVEN Flask application configured for testing and watchdog service is running
    WHEN the '/watchdog' endpoint is requested (POST) with 'start' option
    THEN check that a '400' code is returned
    """
    headers = {
        "Content-Type": "application/json",
    }
    post_data = {
        'watchdog': 'start'
    }
    response = test_client.post('/watchdog', headers=headers, data=json.dumps(post_data))
    assert response.status_code == 400


def test_watchdog_stop(test_client):
    """
    GIVEN Flask application configured for testing
    WHEN the '/watchdog' endpoint is requested (POST) and watchdog service is running
    THEN watchdog service is down
    """
    headers = {
        "Content-Type": "application/json",
    }
    post_data = {
        'watchdog': 'stop'
    }
    response = test_client.post('/watchdog', headers=headers, data=json.dumps(post_data))
    assert response.status_code == 200


def test_watchdog_stop_when_not_running(test_client):
    """
    GIVEN Flask application configured for testing
    WHEN the '/watchdog' endpoint is requested (POST) and watchdog service is not running
    THEN check that a '400' code is returned
    """
    headers = {
        "Content-Type": "application/json",
    }
    post_data = {
        'watchdog': 'stop'
    }
    response = test_client.post('/watchdog', headers=headers, data=json.dumps(post_data))
    assert response.status_code == 400


def test_delete_all_services(test_client):
    """
    GIVEN Flask application configured for testing
    WHEN the '/services' endpoint is requested (DELETE)
    THEN check that a '200' code is returned and all services have been deleted
    """
    response = test_client.delete('/services')
    assert response.status_code == 200
    # Check whether all services have been deleted from db
    response = test_client.get('/services')
    json_data = response.get_json()
    assert len(json_data['data']['services']) == 0

