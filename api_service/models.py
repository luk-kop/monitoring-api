from datetime import datetime

from api_service.extensions import db


class Service(db.Document):
    name = db.StringField(max_length=30, required=True, unique=True)
    host = db.StringField(max_length=30, required=True)
    port = db.StringField(max_length=8, required=True)
    proto = db.StringField(max_length=3, choices=('tcp', 'udp'))
    last_responded = db.DateTimeField()
    last_configured = db.DateTimeField(default=datetime.utcnow())
    service_up = db.BooleanField(required=True, default=False)

    def to_dict(self):
        """
        Render model as dict
        :return: dict
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'port': self.port,
            'proto': self.proto,
            'last_responded': self.last_responded.isoformat() if self.last_responded else None,
            'last_configured': self.last_configured.isoformat(),
            'service_up': self.service_up
        }