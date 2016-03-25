# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20160127_2019'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='event_note',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
