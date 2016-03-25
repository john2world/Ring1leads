# TODO: function to return fields required by qscore
# TODO: function to return mapped fields

from django.db import models

from program_manager.models import Program


class MappedField(models.Model):
    program = models.ForeignKey(Program, related_name='mapped_fields')

    from_field = models.CharField(max_length=255)
    to_field = models.CharField(max_length=255)
