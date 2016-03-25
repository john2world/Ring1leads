import json
import datetime
from django.core.exceptions import ObjectDoesNotExist


def django_model_instance_to_json(instance, depth=1):

    def dt_handler(obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        return None

    return json.dumps(django_model_instance_to_dict(instance, depth), default=dt_handler)


def django_model_instance_to_dict(instance, depth=1, ignore_model=None):
    """
    Transform Django model instance to python dictionary
    :param instance: Django model instance:
    :param depth: int value represents how many levels of related models should be serialized
    :param ignore_model: skip serialization of this Model
    :return: Django model instance as python dict
    """
    data = {}

    if not instance:
        return data

    if ignore_model is None:
        ignore_model = instance._meta.model

    for field in instance._meta.get_fields():

        field_name = field.name

        if field.is_relation:

            if depth:
                if field.one_to_many:
                    related_name = field.related_name
                    if not related_name:
                        related_name = '%s_set' % field_name

                    related_manager = getattr(instance, related_name)
                    related_instances = related_manager.all()
                    related_data = []
                    for related_instance in related_instances:
                        related_data.append(django_model_instance_to_dict(related_instance, depth - 1, ignore_model))

                    data[related_name] = related_data

                if field.many_to_one or field.one_to_one:
                    try:
                        data[field_name] = django_model_instance_to_dict(getattr(instance, field_name), depth - 1, ignore_model)
                    except ObjectDoesNotExist:
                        pass

        else:
            data[field_name] = getattr(instance, field_name)
    return data
