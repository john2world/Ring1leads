# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogsReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('program', models.OneToOneField(to='program_manager.Program')),
            ],
        ),
        migrations.CreateModel(
            name='QualityScoreReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('program', models.OneToOneField(to='program_manager.Program')),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('records', models.PositiveIntegerField(default=0)),
                ('duplicate_groups', models.PositiveIntegerField(default=0)),
                ('duplicate_records', models.PositiveIntegerField(default=0)),
                ('normalized_records', models.PositiveIntegerField(default=0)),
                ('junk_records', models.PositiveIntegerField(default=0)),
                ('program', models.ForeignKey(to='program_manager.Program')),
            ],
        ),
    ]
