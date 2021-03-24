from datetime import datetime

from api_service.extensions import db


class Timestamps(db.EmbeddedDocument):
    """
    Model representing the 'timestamps' field of the 'service' document.
    """
    last_responded = db.DateTimeField()
    last_tested = db.DateTimeField()
    created = db.DateTimeField(default=datetime.utcnow())
    edited = db.DateTimeField(default=datetime.utcnow())


class Host(db.EmbeddedDocument):
    """
    Model representing the 'host' field of the 'service' document.
    """
    type = db.StringField(choices=('hostname', 'ip'), required=True)
    value = db.StringField(max_length=30, required=True)


class Service(db.Document):
    """
    Model representing a 'service' document in MongoDB.
    """
    name = db.StringField(max_length=30, required=True, unique=True)
    host = db.EmbeddedDocumentField(document_type=Host)
    port = db.StringField(max_length=8, required=True)
    proto = db.StringField(choices=('tcp', 'udp'), required=True)
    timestamps = db.EmbeddedDocumentField(document_type=Timestamps, default=Timestamps)
    service_up = db.BooleanField(required=True, default=False)




