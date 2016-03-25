# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0004_auto_20160211_2006'),
    ]

    operations = [
        migrations.CreateModel(
            name='JunkRemovalSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('delete_spam_records', models.BooleanField(default=True)),
            ],
        ),
        migrations.AlterField(
            model_name='program',
            name='junk_removal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='junkremovalsettings',
            name='program',
            field=annoying.fields.AutoOneToOneField(related_name='junk_removal_settings', null=True, blank=True, to='program_manager.Program'),
        ),
    ]
