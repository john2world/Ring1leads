import re
import json
from functools import wraps
from django.utils.decorators import available_attrs, method_decorator
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.cache import add_never_cache_headers


def json_to_jsonp(request, response):
    callback = request.GET.get('callback', 'callback')
    if not re.match(r'\w+$', callback):
        return HttpResponseForbidden(json.dumps({'error': 'Only alphanumeric characters are allowed as the callback name.'}), content_type='application/json')
    return HttpResponse('%s(%s)' % (callback, response.content),
            content_type='application/json')

class JSONPMiddleware(object):
    '''
    Transforms a regular HTTPResponse containing JSON to a JSONP response.
    Handles callback naming and validation.
    '''

    def process_response(self, request, response):
        if request.GET.get('force_json'):
            return response
        if response.get('Content-Type', '').split(';')[0] == 'application/json':
            return json_to_jsonp(request, response)
        else:
            return response

def jsonp(function):
    '''
    Transforms a regular HTTPResponse containing JSON to a JSONP response.
    Handles callback naming and validation.
    '''
    def decorator(view):
        @wraps(view, assigned=available_attrs(function))
        def _wrapped_view(request, *args, **kwargs):
            response = view(request, *args, **kwargs).content
            return json_to_jsonp(request, response)
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator

class JSONPMixin(object):
    '''
    Transforms a regular HTTPResponse containing JSON to a JSONP response.
    Handles callback naming and validation.
    '''

    @method_decorator(jsonp)
    def dispatch(self, request, *args, **kwargs):
        return super(JSONPMixin, self).dispatch(request, *args, **kwargs)


class DisableClientSideCachingMiddleware(object):
    def process_response(self, request, response):
        add_never_cache_headers(response)
        return response
