from api_service import init_celery


app = init_celery()
app.conf.imports = app.conf.imports + ('api_service.watchdog_celery.tasks',)