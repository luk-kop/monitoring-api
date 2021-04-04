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
    The default sorting operation is - sort objects ascending by id.
    """
    def __init__(self, iterable, after_id, before_id, page_limit, sort_by):
        self.iterable = iterable
        self.after_id = after_id
        self.before_id = before_id
        self.page_limit = page_limit
        if sort_by:
            if sort_by[0] == '-':
                self.sort_dir = 'descending'
                self.sort_by = sort_by[1:]
            else:
                self.sort_dir = 'ascending'
                self.sort_by = sort_by
        else:
            # Default sorting
            self.sort_by = 'id'
            self.sort_dir = 'ascending'

        if isinstance(iterable, QuerySet):
            self.total = iterable.count()
        else:
            self.total = len(iterable)
        if after_id:
            # Execute if 'after' query param is present in URL
            model = iterable(id=after_id).first()
            # Calculate the next page of items (page after model with 'after_id' id)
            if self.sort_dir == 'ascending':
                items_kwargs = {
                    f'{self.sort_by}__gt': getattr(model, f'{self.sort_by}')
                }
                self.items = iterable(**items_kwargs).limit(page_limit)
            else:
                items_kwargs = {
                    f'{self.sort_by}__lt': getattr(model, f'{self.sort_by}')
                }
                self.items = iterable(**items_kwargs).order_by(f'-{self.sort_by}').limit(page_limit)
        elif before_id:
            # Execute if 'before' query param is present in URL
            model = iterable(id=before_id).first()
            # Calculate the prev page of items (page before model with 'after_id' id)
            if self.sort_dir == 'ascending':
                items_kwargs = {
                    f'{self.sort_by}__lt': getattr(model, f'{self.sort_by}')
                }
                self.items = iterable(**items_kwargs).limit(page_limit)
            else:
                items_kwargs = {
                    f'{self.sort_by}__gt': getattr(model, f'{self.sort_by}')
                }
                self.items = iterable(**items_kwargs).order_by(f'-{self.sort_by}').limit(page_limit)
            skip_count = self.items.count() - page_limit
            if skip_count >= 0:
                self.items = self.items.skip(skip_count)
        else:
            # Execute if neither 'before' nor 'after' query params are present in URL
            if self.sort_dir == 'ascending':
                self.items = iterable.order_by(self.sort_by).limit(page_limit)
            else:
                self.items = iterable.order_by(f'-{self.sort_by}').limit(page_limit)
        try:
            # '_last_item' on the page - necessary to determine the new 'after'
            self._last_item = self.items[self.items_count - 1]
            # Check whether there are any objects in db behind '_last_item'
            if self.sort_dir == 'ascending':
                items_kwargs = {
                    f'{self.sort_by}__gt': getattr(self._last_item, f'{self.sort_by}')
                }
            else:
                items_kwargs = {
                    f'{self.sort_by}__lt': getattr(self._last_item, f'{self.sort_by}')
                }
            self._items_count_after_last_item = len(self.iterable(**items_kwargs))
        except IndexError:
            self._last_item = None
        # '_first_item' on the page - necessary to determine the new 'before'
        self._first_item = self.items.first()
        if self._first_item:
            # Check whether there are any objects in db before '_firs_item'
            if self.sort_dir == 'ascending':
                items_kwargs = {
                    f'{self.sort_by}__lt': getattr(self._first_item, f'{self.sort_by}')
                }
            else:
                items_kwargs = {
                    f'{self.sort_by}__gt': getattr(self._first_item, f'{self.sort_by}')
                }
            self._items_count_before_first_item = len(self.iterable(**items_kwargs))

    @property
    def after(self):
        """
        Returns 'after' cursor (starting next page after this cursor).
        """
        if self._last_item:
            if self.items_count <= self.page_limit and self._items_count_after_last_item > 0:
                return self._last_item
        return None

    @property
    def before(self):
        """
        Returns 'before' cursor (starting previous page before this cursor).
        """
        if self._first_item:
            if self.items_count <= self.page_limit and self._items_count_before_first_item > 0:
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
    def paginate_cursor(cls, **kwargs):
        """
        Add cursor-based pagination to Service model.
        """
        return PaginationCursor(cls.objects, **kwargs)




