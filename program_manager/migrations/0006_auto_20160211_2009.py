# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0005_auto_20160211_2007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='program',
            name='junk_removal',
            field=models.BooleanField(default=True),
        ),
    ]
