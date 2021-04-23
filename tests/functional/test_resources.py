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
    # post_data = {
    #     'name': 'test-service-01',
    #     'host': {
    #         'type': 'ip',
    #         'value': '192.168.1.10'
    #     },
    #     'proto': 'tcp',
    #     'port': '1111'
    # }
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
    # post_data = {
    #     'name': 'test-service-01',
    #     'host': {
    #         'type': 'ip',
    #         'value': '192.168.1.10'
    #     },
    #     'proto': 'tcp',
    #     'port': '1111'
    # }
    post_data = example_service_data
    headers = {
        "Content-Type": "application/json",
    }
    response = test_client.post('/services', headers=headers, data=json.dumps(example_service_data))
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
    for proto in ['smtp', 123, 'http']:
        post_data['proto'] = proto
        response = test_client.post('/services', headers=headers, data=json.dumps(post_data))
        assert response.status_code == 400
    # Wrong port
    for port in ['0', 'smtp', 123, 'http', '66666']:
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
    WHEN the '/services{service_id}' endpoint is requested (DELETE)
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


# TODO: test for put and patch


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

