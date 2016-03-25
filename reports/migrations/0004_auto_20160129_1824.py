# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_report_date_completed_estimate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ['-date_created']},
        ),
        migrations.AlterField(
            model_name='report',
            name='program',
            field=models.ForeignKey(related_name='reports', to='program_manager.Program'),
        ),
    ]
