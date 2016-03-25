from django import template
from django.conf import settings
from django.utils.html import escape

register = template.Library()

@register.simple_tag
def app_version():
    return escape(settings.APP_VERSION)
