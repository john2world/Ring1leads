# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event_type', models.CharField(max_length=30)),
                ('event_data', jsonfield.fields.JSONField()),
                ('event_expiration', models.DurationField(default=datetime.timedelta(1))),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='events', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-date_created',),
            },
        ),
        migrations.CreateModel(
            name='EventConsumed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(related_name='consumed', to='events.Event')),
                ('user', models.ForeignKey(related_name='consumed_events', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
