# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0011_program_schedule_enabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='schedule_hour',
            field=models.TimeField(null=True),
        ),
    ]
