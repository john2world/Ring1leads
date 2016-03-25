# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0006_auto_20160211_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='paused',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='survivingrecordrule',
            name='rule',
            field=models.CharField(default=b'NEWEST', max_length=256, choices=[(b'NEWEST', b'is newest value'), (b'OLDEST', b'is oldest value'), (b'LOWEST_VALUE', b'is the lowest value'), (b'HIGHEST_VALUE', b'is the highest value'), (b'IS', b'is'), (b'NOT', b'is not'), (b'CONTAINS', b'contains'), (b'STARTS', b'starts with'), (b'TRUE', b'True'), (b'FALSE', b'False')]),
        ),
    ]
