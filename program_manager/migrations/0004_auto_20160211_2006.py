# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0003_auto_20160129_1824'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='junkremovalsettings',
            name='program',
        ),
        migrations.AlterField(
            model_name='program',
            name='junk_removal',
            field=models.BooleanField(default=True),
        ),
        migrations.DeleteModel(
            name='JunkRemovalSettings',
        ),
    ]
