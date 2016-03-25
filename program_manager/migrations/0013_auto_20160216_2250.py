# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0012_auto_20160216_2103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='schedule_day',
            field=models.CharField(default=b'0', max_length=64, null=True, choices=[(b'0', b'Monday'), (b'1', b'Tuesday'), (b'2', b'Wednesday'), (b'3', b'Thursday'), (b'4', b'Friday'), (b'5', b'Saturday'), (b'6', b'Sunday')]),
        ),
        migrations.AlterField(
            model_name='program',
            name='tags',
            field=models.CharField(max_length=2048, null=True, blank=True),
        ),
    ]
