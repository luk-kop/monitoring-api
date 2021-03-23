from datetime import datetime

from api_service.extensions import db


class Timestamps(db.EmbeddedDocument):
    """
    Model representing the 'timestamps' field of the 'service' document.
    """
    last_configured = db.DateTimeField(default=datetime.utcnow())
    last_responded = db.DateTimeField()
    last_tested = db.DateTimeField()
    created_at = db.DateTimeField(default=datetime.utcnow())


class Host(db.EmbeddedDocument):
    """
    Model representing the 'host' field of the 'service' document.
    """
    type = db.StringField()
    value = db.StringField()


class Service(db.Document):
    """
    Model representing a 'service' document in MongoDB.
    """
    name = db.StringField(max_length=30, required=True, unique=True)
    host = db.EmbeddedDocumentField(Host)
    port = db.StringField(max_length=8, required=True)
    proto = db.StringField(max_length=3, choices=('tcp', 'udp'))
    timestamps = db.EmbeddedDocumentField(Timestamps)
    service_up = db.BooleanField(required=True, default=False)




