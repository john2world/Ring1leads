# coding: utf-8

from django import template
from django.utils.dateparse import parse_datetime


register = template.Library()


@register.filter('parse_datetime')
def parse_datetime_filter(date_string):
    """
    Return a datetime corresponding to date_string, parsed according to DATETIME_INPUT_FORMATS
    For example, to re-display a date string in another format::
    {{ "01/01/1970"|parse_datetime|date:"F jS, Y" }}
    """

    try:
        return parse_datetime(date_string)
    except Exception:
        return date_string
