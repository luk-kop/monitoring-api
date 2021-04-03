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
    def __init__(self, iterable, after_id, before_id, page_limit):
        self.iterable = iterable
        self.after_id = after_id
        self.before_id = before_id
        self.page_limit = page_limit

        if isinstance(iterable, QuerySet):
            self.total = iterable.count()
        else:
            self.total = len(iterable)

        if after_id:
            # Get 'page_limit' documents from db with 'id' > 'after_id'
            self.items = iterable(id__gt=after_id).limit(page_limit)
        elif before_id:
            # Get 'page_limit' documents from db with 'id' < 'before_id'
            self.items = iterable(id__lt=before_id)
            skip_count = self.items.count() - page_limit
            if skip_count >= 0:
                self.items = self.items.skip(skip_count)
            # db.collection.find().skip(db.collection.count() - N)
        else:
            # Get the first 'page_limit' documents from db
            self.items = iterable().limit(page_limit)
        try:
            # '_last_item' necessary to determine the new 'after'
            self._last_item = self.items[self.items_count - 1]
        except IndexError:
            self._last_item = None
        try:
            # '_first_item' necessary to determine the new 'before'
            self._first_item = self.items.first()
        except IndexError:
            self._first_item = None

    @property
    def after(self):
        """
        Returns 'after' cursor (starting next page after this cursor).
        """
        if self._last_item:
            if self.items_count <= self.page_limit and len(self.iterable(id__gt=self._last_item.id)) > 0:
                return self._last_item
        return None

    @property
    def before(self):
        """
        Returns 'before' cursor (starting previous page before this cursor).
        """
        if self._first_item:
            if self.items_count <= self.page_limit and len(self.iterable(id__lt=self._first_item.id)) > 0:
                return self._first_item
        return None

    @property
    def items_count(self):
        """
        Returns number of items.
        """
        return len(self.items)


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
    name = db.StringField(max_length=40, required=True, unique=True)
    host = db.EmbeddedDocumentField(document_type=Host)
    port = db.StringField(max_length=8, required=True)
    proto = db.StringField(choices=('tcp', 'udp'), required=True)
    timestamps = db.EmbeddedDocumentField(document_type=Timestamps, default=Timestamps)
    service_up = db.BooleanField(required=True, default=False)

    @classmethod
    def paginate_cursor(cls, after_id, before_id, page_limit, **kwargs):
        """
        Add cursor-based pagination to Service model.
        """
        return PaginationCursor(cls.objects, after_id, before_id, page_limit)




