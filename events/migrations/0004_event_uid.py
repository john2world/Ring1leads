# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_event_event_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='uid',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
    ]
