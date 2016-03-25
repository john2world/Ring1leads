from django.db import models
from django.forms import model_to_dict
from rest_framework.renderers import JSONRenderer
from project_utils.common import import_to_python


class SerializableQuerySet(models.QuerySet):
    def to_dict(self, serializer=None):
        if not hasattr(self.model, 'get_serializer'):
            raise NotImplementedError('Model must implement get_serializer method')

        serializer = serializer or self.model.get_serializer()
        return serializer(self, many=True).data

    def to_json(self, serializer=None):
        return JSONRenderer().render(self.to_dict(serializer))


class SerializableModelMixin(object):
    """
    >> program.to_dict()  # would use api.serializers.ProgramSerializer
    >> program.to_dict(serializer=ProgramVerboseSerializer)
    """
    @property
    def serializer(self):
        serializer = self.get_serializer()
        return serializer(self)

    @classmethod
    def get_serializer(cls):
        import_path = 'api.serializers.{0}Serializer'.format(cls.__name__)
        return import_to_python(import_path)

    def to_dict(self, serializer=None):
        return dict(self.to_ordered_dict(serializer))

    def to_ordered_dict(self, serializer=None):
        serializer = serializer or self.get_serializer()
        return serializer(self).data

    def to_json(self, serializer=None):
        return JSONRenderer().render(self.to_ordered_dict(serializer))


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict

        diffs = []
        for k, v in d1.items():
            try:
                if v != d2[k]:
                    diffs.append((k, (v, d2[k])))
            except TypeError:  # e.g. "can't compare offset-naive and offset-aware datetimes"
                continue  # TODO: handle offset-naive and offset-aware datetime comparison

        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in self._meta.fields])
