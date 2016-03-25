# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QualityScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('score', models.PositiveSmallIntegerField(null=True)),
                ('percent_valid_location', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('percent_valid_phone', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('percent_valid_email', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('percent_spam_email', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('percent_complete', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('avg_age', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('avg_since_last_modified', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('progress', models.CharField(max_length=255, blank=True)),
                ('program', models.ForeignKey(to='program_manager.Program')),
            ],
        ),
    ]
