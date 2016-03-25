# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_reports(apps, schema):
    Report = apps.get_model('reports.Report')

    Report.objects.filter(
        date_completed=None
    ).update(
        date_completed=models.F('date_created')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='date_completed',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='report',
            name='is_current',
            field=models.NullBooleanField(),
        ),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together=set([('program', 'is_current')]),
        ),

        migrations.RunPython(populate_reports),
    ]
