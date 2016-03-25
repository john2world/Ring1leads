# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('integrations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactsNormalizerRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField()),
                ('broadlook_field_name', models.CharField(max_length=256)),
                ('broadlook_rule_name', models.CharField(max_length=256)),
                ('rule', models.CharField(max_length=256)),
                ('field', models.ForeignKey(to='integrations.ExternalField')),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
        migrations.CreateModel(
            name='DupMatchRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField()),
                ('rule', models.CharField(default=b'EXACT', max_length=256, choices=[(b'EXACT', b'is an exact match'), (b'SIMILAR', b'is very similar'), (b'LOOSE', b'is somewhat similar')])),
                ('field', models.ForeignKey(to='integrations.ExternalField')),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
        migrations.CreateModel(
            name='FieldFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('operator', models.CharField(default=b'=', max_length=256, choices=[(b'IS', b'is'), (b'NOT', b'is not'), (b'CONTAINS', b'contains'), (b'STARTS', b'starts with'), (b'=', b'equals'), (b'>', b'is greater than'), (b'<', b'is less than'), (b'DATE_EXACT', b'is'), (b'DATE_AFTER', b'is after'), (b'DATE_BEFORE', b'is before'), (b'TRUE', b'True'), (b'FALSE', b'False')])),
                ('field_value', models.CharField(max_length=256, null=True, blank=True)),
                ('field', models.ForeignKey(to='integrations.ExternalField')),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('progress', models.PositiveSmallIntegerField(default=0)),
                ('task_id', models.CharField(unique=True, max_length=128)),
                ('status', models.CharField(default=b'PENDING', max_length=128, choices=[(b'PENDING', b'Pending'), (b'STARTED', b'Started'), (b'RETRY', b'Retrying'), (b'FAILURE', b'Failure'), (b'SUCCESS', b'Success')])),
            ],
        ),
        migrations.CreateModel(
            name='JunkRemovalSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('delete_spam_records', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LocationOptimizationRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField()),
                ('rule', models.CharField(default=b'OVERWRITE', max_length=256, choices=[(b'OVERWRITE', b'Overwrite'), (b'UPDATE_IF_BLANK', b'Update if blank'), (b'DO_NOT_UPDATE', b"Don't update")])),
                ('field', models.ForeignKey(to='integrations.ExternalField')),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_run', models.DateTimeField(null=True, blank=True)),
                ('name', models.CharField(max_length=256, null=True)),
                ('status', models.CharField(default=b'CREA', max_length=256, choices=[(b'CREA', b'Creating'), (b'PEND', b'Pending'), (b'CANCEL', b'Cancelled'), (b'RUN', b'Running'), (b'PAUSE', b'Paused'), (b'ERROR', b'Error'), (b'COMPL', b'Completed'), (b'ACT', b'Active'), (b'ARCH', b'Archived')])),
                ('dedupe', models.BooleanField(default=True)),
                ('analyze_only', models.BooleanField(default=False)),
                ('location_optimization', models.BooleanField(default=False)),
                ('contacts_normalization', models.BooleanField(default=True)),
                ('junk_removal', models.BooleanField(default=False)),
                ('pre_backup_url', models.URLField(max_length=256, null=True, blank=True)),
                ('post_run_url', models.URLField(max_length=256, null=True, blank=True)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_program_manager.program_set+', editable=False, to='contenttypes.ContentType', null=True)),
                ('source', models.ForeignKey(related_name='programs', to='integrations.Source', null=True)),
                ('table_schema', models.ForeignKey(to='integrations.ExternalTable', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='SurvivingRecordRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField()),
                ('rule', models.CharField(default=b'NEWEST', max_length=256, choices=[(b'OLDEST', b'is oldest value'), (b'NEWEST', b'is newest value'), (b'LOWEST_VALUE', b'is the lowest value'), (b'HIGHEST_VALUE', b'is the highest value'), (b'IS', b'is'), (b'NOT', b'is not'), (b'CONTAINS', b'contains'), (b'STARTS', b'starts with'), (b'TRUE', b'True'), (b'FALSE', b'False')])),
                ('value', models.CharField(max_length=256, null=True, blank=True)),
                ('field', models.ForeignKey(to='integrations.ExternalField')),
                ('program', models.ForeignKey(to='program_manager.Program', null=True)),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
        migrations.CreateModel(
            name='SurvivingValueRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField()),
                ('rule', models.CharField(default=b'ADD', max_length=256, choices=[(b'OLDEST', b'keep the oldest value'), (b'NEWEST', b'keep the newest value'), (b'NUMADD', b'add all values'), (b'NUMAVG', b'take an average of all values'), (b'NUMMAX', b'keep the highest value'), (b'NUMMIN', b'keep the lowest value'), (b'CONCAT', b'concatenate all text'), (b'IS', b'is'), (b'NOT', b'is not'), (b'CONTAINS', b'contains'), (b'STARTS', b'starts with'), (b'PICKLIST_HIERARCHY', b'prioritize'), (b'TRUE', b'True'), (b'FALSE', b'False')])),
                ('value', models.CharField(max_length=256, null=True, blank=True)),
                ('field', models.ForeignKey(to='integrations.ExternalField')),
                ('program', models.ForeignKey(to='program_manager.Program', null=True)),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
        migrations.CreateModel(
            name='TableFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('table_name', models.CharField(max_length=256)),
                ('program', models.ForeignKey(blank=True, to='program_manager.Program', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='locationoptimizationrule',
            name='program',
            field=models.ForeignKey(related_name='location_optimization_rules', blank=True, to='program_manager.Program', null=True),
        ),
        migrations.AddField(
            model_name='junkremovalsettings',
            name='program',
            field=annoying.fields.AutoOneToOneField(related_name='junk_removal_settings', null=True, blank=True, to='program_manager.Program'),
        ),
        migrations.AddField(
            model_name='job',
            name='program',
            field=models.ForeignKey(to='program_manager.Program'),
        ),
        migrations.AddField(
            model_name='fieldfilter',
            name='program',
            field=models.ForeignKey(to='program_manager.Program', null=True),
        ),
        migrations.AddField(
            model_name='dupmatchrule',
            name='program',
            field=models.ForeignKey(blank=True, to='program_manager.Program', null=True),
        ),
        migrations.AddField(
            model_name='contactsnormalizerrule',
            name='program',
            field=models.ForeignKey(related_name='contacts_normalizer_rules', blank=True, to='program_manager.Program', null=True),
        ),
    ]
