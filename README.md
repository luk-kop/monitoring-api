# Monitoring API

[![Python 3.8.5](https://img.shields.io/badge/python-3.8.5-blue.svg)](https://www.python.org/downloads/release/python-377/)
[![Flask-RESTful 0.3.8](https://img.shields.io/badge/Flask--RESTful-0.3.8-blue.svg)](https://flask-restful.readthedocs.io/en/latest/)
[![Celery 5.0.5](https://img.shields.io/badge/Celery-5.0.5-blue.svg)](https://docs.celeryproject.org/en/stable/)
[![celery-redbeat 2.0.0](https://img.shields.io/badge/celery--redbeat-2.0.0-blue.svg)](https://pypi.org/project/celery-redbeat/)
[![Flask-MongoEngine 1.0.0](https://img.shields.io/badge/Flask--MongoEngine-1.0.0-blue.svg)](http://docs.mongoengine.org/projects/flask-mongoengine/en/latest/)
[![marshmallow 3.10.0](https://img.shields.io/badge/marshmallow-3.10.0-blue.svg)](https://marshmallow.readthedocs.io/en/stable/)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

> The **Monitoring API** is a simple REST API based on **Flask-RESTful** library. The main purpose of the application is to monitor the availability of selected services. The application checks at regular intervals the availability of services on the specified ip address (or hostname) and port (TCP or UDP).


## Features
* The monitored services data is stored in the **MongoDB** database (details and status of services).
* The monitored services are specified using:
    - ip address or hostname (DNS);
    - transport protocol - TCP or UDP;
    - network port.
* Service monitoring feature (**watchdog** service) can be activated and deactivated on demand with a dedicated endpoint.
* Service monitoring feature (**watchdog** service) is executed as background task with **Celery** (worker), **celery-redbeat** (beat scheduler) and **Redis** (broker and result backend).
* Service status is determined by the availability of the monitored host port.
* The monitored can have the following availability status:
    - `up` - service is available (**watchdog** service is running);
    - `down` - service not available (**watchdog** service is running);
    - `unknown` - service status is unknown because **watchdog** service is not running.
* The application allows the user to add services to be monitored.
* The user can modify and delete selected service. Moreover, it is possible to delete all services from the database with a single endpoint.
* All monitored services can be returned by application.
* Sorting and pagination (cursor-based) functionalities has been implemented. The returned services can be sorted by id (MongoDB `_id`) or name.
* Interactive API documentation with Swagger UI (OpenAPI v2.0 specification)

## Getting Started

Below instructions will get you a copy of the project running on your local machine.

### Requirements
Python third party packages:
* [Flask](https://flask.palletsprojects.com/en/1.1.x/)
* [Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/)
* [Flask-MongoEngine](http://docs.mongoengine.org/projects/flask-mongoengine/en/latest/)
* [Celery](https://docs.celeryproject.org/en/stable/)
* [celery-redbeat](https://pypi.org/project/celery-redbeat/)
* [PyMongo](https://pymongo.readthedocs.io/en/stable/)
* [marshmallow](https://marshmallow.readthedocs.io/en/stable/)
* [flasgger](https://github.com/flasgger/flasgger)
* [python-dotenv](https://pypi.org/project/python-dotenv/)
* [pytest](https://docs.pytest.org/en/6.2.x/)

Other prerequisites:
* The monitored host should have a firewall rule added allowing to query the monitored service port by the ip address where the **Monitoring API** will be run.
  This is necessary to obtain reliable data about the availability of the monitored services.
* Under the hood application use `netcat` and `nmap` packages to test host's availability. 
  For this reason, it is **recommended** to run the application using the `docker-compose` tool with already prepared dockerfiles.
* If you intend to run the application locally without using `docker-compose` (**not recommended**): 
  - you will need to install the `netcat` and `nmap` packages and allow application to run `nmap` with elevated privileges (e.g by adding an entry `your-username ALL = (ALL) NOPASSWD: /usr/bin/nmap` to `/etc/sudoers`).
  - run the **MongoDB**, **Redis** and **Celery** worker.

  
## Build and run the app with Docker-Compose
The recommended way to run application is to build it with `docker-compose` tool.

In order to correctly start the application, you must run the following commands in the project root directory (`monitoring-api`).

1. Before running `docker-compose` command you should create `.env-web`, `.env-mongo`, `.env-express` and `.env-worker` files. The best solution is to copy the existing example files and edit the necessary data.
```bash
# Create required environment files using examples from repository
$ cp docker/web/.env-web-example docker/web/.env-web
$ cp docker/mongo/.env-mongo-example docker/mongo/.env-mongo
$ cp docker/mongo-express/.env-express-example docker/mongo-express/.env-express
$ cp docker/worker/.env-worker-example docker/worker/.env-worker
```
2. Build and start containers using the commands shown below:
```bash
# To build containers specified in docker-compose.yml file
$ docker-compose build
# To start containers (add -d to run them in the background)
$ docker-compose up -d
# To verify status of the application:
$ docker-compose ps
```

3. Open `http://localhost:8080/apidocs` in your browser to see the **Monitoring API** Swagger UI documentation.


4. To open **Mongo Express** (web-based MongoDB admin console) enter in browser `http://localhost:8081`.
Login with default credentials:
   - username: `mongo`
   - password: `express`


5. To stop application run:
```bash
$ docker-compose stop
```

## Build and run the app with virtualenv tool
The application can be build and run locally with `virtualenv` tool.
As mentioned in the requirements, to run applications locally you need to install `netcat` and `nmap` packages at the OS level.

1. Run following commands in order to create virtual environment and install the required packages.
    ```bash
    $ virtualenv venv
    $ source venv/bin/activate
    (venv) $ pip install -r requirements.txt
    ```

2. Before running application you should create `.env` file in the root application directory (`monitoring-api`).
   The best solution is to copy the existing example file `.env-example` and edit the necessary data.
    ```bash
    $ cp .env-example .env
    ```

3. Run the **MongoDB**, **Redis** and **Celery** worker:
   
   The fastest and easiest way to start MongoDB and Redis is to use `docker` tool:
    ```bash
    $ docker run --name mongo-api -d -p 27017:27017 mongo
    $ docker run --name redis-api --user redis -d -p 6379:6379 redis
    ````
    Run another (second) terminal session and in `monitoring-api` directory enter the following commands to run Celery worker:
    ```bash
    $ source venv/bin/activate
    $ (venv} $ celery -A api_service.watchdog_celery.tasks.celery_app worker --beat --loglevel=info
    ```
4. Set the `FLASK_APP` environment variable to point `run.py` script and then invoke `flask run` command.
    ```bash
    (venv) $ export FLASK_APP=run.py
    (venv) $ flask run 
    ```

## Monitoring API Endpoints
Below you can find the list of API endpoints (view from Swagger UI - `http://localhost:8080/apidocs`).

![Application endpoints](./images/flassger-enpoints.png)

## Examples of requests to the API
Using the following requests, you can interact with the API using the `curl` tool. The following examples refer to `docker-compose` deployment.

- List all services:
    ```bash
    curl -X GET -H "Content-Type: application/json" http://localhost:8080/services
    ```
- Create new service:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"name": "dns-google-01", "host": {"type": "ip", "value": "8.8.8.8"}, "proto": "udp", "port": "53"}' \
      http://localhost:8080/services
    ```
- Delete all services:
    ```bash
    curl -X DELETE -H "Content-Type: application/json" http://localhost:8080/services
    ```
- Find specific service by id:
    ```bash
    curl -X GET -H "Content-Type: application/json" http://localhost:8080/services/6089dfa19f1da51c7a8670ad
    ```
- Update an existing service by id:
    ```bash
    curl -X PUT -H "Content-Type: application/json" \
      -d '{"name": "dns-google-02", "host": {"type": "ip", "value": "8.8.4.4"}, "proto": "udp", "port": "53"}' \
      http://localhost:8080/services/6089dfa19f1da51c7a8670ad
    ```
- Update an existing service's properties by id:
    ```bash
    curl -X PATCH -H "Content-Type: application/json" \
      -d '{"name": "dns-public-server-01"}' \
      http://localhost:8080/services/6089dfa19f1da51c7a8670ad
    ```
- Delete an existing service by id:
    ```bash
    curl -X DELETE -H "Content-Type: application/json" http://localhost:8080/services/6089dfa19f1da51c7a8670ad
    ```
- Check status of the watchdog service:
    ```bash
    curl -X GET -H "Content-Type: application/json" http://localhost:8080/watchdog
    ```
- Start the watchdog service:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
    -d '{"watchdog": "start"}' \
    http://localhost:8080/watchdog
    ```
- Stop the watchdog service:
    ```bash
    curl -X POST -H "Content-Type: application/json" \
    -d '{"watchdog": "stop"}' \
    http://localhost:8080/watchdog
    ```
## Testing

Tests should be run locally (inside virtual environment - `venv`) with MongoDB and Redis running. 
After starting the application, run all tests with the following command:
```bash
(venv) $ pytest -v
```