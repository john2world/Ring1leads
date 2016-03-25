# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0010_auto_20160216_1916'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='schedule_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
