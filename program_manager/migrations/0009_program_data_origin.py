# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('program_manager', '0008_program_resume_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='program',
            name='data_origin',
            field=models.CharField(default=b'SALESFORCE', max_length=32, null=True, blank=True, choices=[(b'SALESFORCE', b'Salesforce'), (b'MARKETO', b'Marketo'), (b'TRADESHOWOREVENT', b'Tradeshow or Event'), (b'WEBINAR', b'Webinar'), (b'WEBSITE', b'Website')]),
        ),
    ]
