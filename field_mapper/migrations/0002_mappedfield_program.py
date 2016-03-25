# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0001_initial'),
        ('field_mapper', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mappedfield',
            name='program',
            field=models.ForeignKey(related_name='mapped_fields', to='program_manager.Program'),
        ),
    ]
