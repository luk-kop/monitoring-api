from flask import current_app

from api_service.extensions import api
from api_service.models import Service


def set_services_query_params(data_query_params):
    """
    Set query params for ServicesApi resource.
    """
    page_limit_default = current_app.config.get('DEFAULT_PAGINATION_LIMIT')
    query_params = {
        'after_id': data_query_params.get('after', ''),
        'before_id': data_query_params.get('before', ''),
        'page_limit': data_query_params.get('limit', page_limit_default),
        'sort_by': data_query_params.get('sort', '')
    }
    return query_params


def get_services_to_dump(resource, services, query_params):
    """
    Prepare services data to dump for ServicesApi resource.
    """
    page_limit = query_params.get('page_limit')
    sort_by = query_params.get('sort_by')
    next_url, url_prev, cursor_before, cursor_after = '', '', '', ''
    # Define next and/or prev page url and cursors
    if services.after or services.before:
        url_kwargs = {
            'resource': resource,
            'limit': page_limit,
            '_external': True
        }
        if sort_by:
            url_kwargs['sort'] = sort_by
        if services.after:
            # Get next page url and cursor after
            next_url = api.url_for(**url_kwargs, after=services.after.id)
            cursor_after = str(services.after.id)
        if services.before:
            # Get prev page url and cursor before
            url_prev = api.url_for(**url_kwargs, before=services.before.id)
            cursor_before = str(services.before.id)
    services_count_up = Service.objects(status='up').count()
    paging = {
        'limit': page_limit,
        'cursors': {
            'before': cursor_before,
            'after': cursor_after
        },
        'links': {
            'previous': url_prev,
            'next': next_url
        }
    }
    data = {
        'services_total': services.total,
        'services_up': services_count_up,
        'services': services.items,
    }
    services_to_dump = {
        'paging': paging,
        'data': data
    }
    return services_to_dump
