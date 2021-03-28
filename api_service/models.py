from datetime import datetime

from mongoengine.queryset import QuerySet

from api_service.extensions import db


class Timestamps(db.EmbeddedDocument):
    """
    Model representing the 'timestamps' field of the 'service' document.
    """
    last_responded = db.DateTimeField()
    last_tested = db.DateTimeField()
    created = db.DateTimeField(default=datetime.utcnow())
    edited = db.DateTimeField(default=datetime.utcnow())


class PaginationCursor:
    """
    Custom pagination for 'service' deserialization. Cursor pagination type with 'next' and 'limit' options.
    """
    def __init__(self, iterable, next_id, page_limit):
        self.iterable = iterable
        self.next_id = next_id
        self.page_limit = page_limit

        if isinstance(iterable, QuerySet):
            self.total = iterable.count()
        else:
            self.total = len(iterable)
        print(self.total)

        if next_id:
            # Get 'page_limit' documents from db with 'id' >= 'next_id'
            self.items = iterable(id__gte=next_id).limit(page_limit)
        else:
            # Get the first 'page_limit' documents from db
            self.items = iterable().limit(page_limit)
        try:
            self._last_item = self.items[len(self.items) - 1]
        except IndexError:
            print('error')
            self._last_item = None
        self._current_item = self.items.first()

    @property
    def next(self):
        if self._last_item:
            return self.iterable(id__gt=self._last_item.id).first()
        else:
            return None

    @property
    def current(self):
        return self._current_item


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

    @classmethod
    def paginate_custom(cls, next_id, page_limit, **kwargs):
        return PaginationCursor(cls.objects, next_id, page_limit)




