from api_service.models import Service


def test_new_service_model(init_database):
    """
    GIVEN a Service model
    WHEN a new Service is created
    THEN check model attributes
    """
    result = {
        'name': 'test-service-telnet-03',
        'host': {
            'type': 'hostname',
            'value': 'test123.service.local'
        },
        'proto': 'tcp',
        'port': '23'
    }
    Service(**result).save()
    service = Service.objects().first()
    assert service.name == 'test-service-telnet-03'
    assert service.host.type == 'hostname'
    assert service.host.value == 'test123.service.local'
    assert service.proto == 'tcp'
    assert service.port == '23'
    assert not service.status == 'up'
