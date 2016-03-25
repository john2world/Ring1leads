# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0009_program_data_origin'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='schedule_day',
            field=models.CharField(default=b'MONDAY', max_length=64, null=True, choices=[(b'MONDAY', b'Monday'), (b'TUESDAY', b'Tuesday'), (b'WEDNESDAY', b'Wednesday'), (b'THURSDAY', b'Thursday'), (b'FRIDAY', b'Friday'), (b'SATURDAY', b'Saturday'), (b'SUNDAY', b'Sunday')]),
        ),
        migrations.AddField(
            model_name='program',
            name='schedule_hour',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='program',
            name='data_origin',
            field=models.CharField(default=b'SALESFORCE', max_length=32, null=True, blank=True, choices=[(b'', b'None'), (b'SALESFORCE', b'Salesforce'), (b'MARKETO', b'Marketo'), (b'TRADESHOWOREVENT', b'Tradeshow or Event'), (b'WEBINAR', b'Webinar'), (b'WEBSITE', b'Website')]),
        ),
    ]
