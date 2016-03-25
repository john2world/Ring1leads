# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0007_auto_20160212_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='resume_data',
            field=jsonfield.fields.JSONField(null=True, blank=True),
        ),
    ]
