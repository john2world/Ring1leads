# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0002_program_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='current_activity_description',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='program',
            name='progress',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
