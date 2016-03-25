# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qscore', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='qualityscore',
            name='progress',
        ),
        migrations.AlterField(
            model_name='qualityscore',
            name='program',
            field=models.ForeignKey(related_name='quality_scores', to='program_manager.Program'),
        ),
    ]
