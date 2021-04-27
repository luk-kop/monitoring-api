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
    The default sorting method is to sort objects ascending by id
    """
    def __init__(self, iterable, after_id, before_id, page_limit, sort_by):
        self.iterable = iterable
        self.after_id = after_id
        self.before_id = before_id
        self.page_limit = page_limit
        if sort_by:
            if sort_by.startswith('-'):
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
        # Find items on current page
        self.items = self.calculate_items_on_page()
        try:
            # '_last_item' on the page - necessary to determine the new 'after'
            self._last_item = self.items[self.items_count - 1]
            # Check whether there are any objects in db behind '_last_item'
            query_operator = f'{self.sort_by}__gt' if self.sort_dir == 'ascending' else f'{self.sort_by}__lt'
            items_kwargs = {
                query_operator: getattr(self._last_item, f'{self.sort_by}')
            }
            self._items_count_after_last_item = len(self.iterable(**items_kwargs))
        except IndexError:
            self._last_item = None
        # '_first_item' on the page - necessary to determine the new 'before'
        self._first_item = self.items.first()
        if self._first_item:
            # Check whether there are any objects in db before '_firs_item'
            query_operator = f'{self.sort_by}__lt' if self.sort_dir == 'ascending' else f'{self.sort_by}__gt'
            items_kwargs = {
                query_operator: getattr(self._first_item, f'{self.sort_by}')
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

    def calculate_items_on_page(self):
        """
        Returns items on current page.
        """
        if self.after_id or self.before_id:
            # Execute if 'after' or 'before' query param is present in URL
            model_id = self.after_id if self.after_id  else self.before_id
            model = self.iterable(id=model_id).first()
            if self.sort_dir == 'ascending':
                query_operator = f'{self.sort_by}__gt' if self.after_id else f'{self.sort_by}__lt'
                items_kwargs = {
                    query_operator: getattr(model, f'{self.sort_by}')
                }
                items = self.iterable(**items_kwargs).order_by(f'{self.sort_by}').limit(self.page_limit)
            else:
                query_operator = f'{self.sort_by}__lt' if self.after_id else f'{self.sort_by}__gt'
                items_kwargs = {
                    query_operator: getattr(model, f'{self.sort_by}')
                }
                items = self.iterable(**items_kwargs).order_by(f'-{self.sort_by}').limit(self.page_limit)
        else:
            # Execute if neither 'before' nor 'after' query params are present in URL
            sort_order = self.sort_by if self.sort_dir == 'ascending' else f'-{self.sort_by}'
            items = self.iterable.order_by(sort_order).limit(self.page_limit)
        return items


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
    status = db.StringField(choices=('up', 'down', 'unknown'), default='unknown')

    @classmethod
    def paginate_cursor(cls, **kwargs):
        """
        Add cursor-based pagination to Service model.
        """
        return PaginationCursor(cls.objects, **kwargs)




