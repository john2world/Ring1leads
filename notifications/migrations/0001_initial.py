# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('subject', models.CharField(max_length=256)),
                ('text', models.TextField()),
                ('sharedwith', models.CharField(default=b'::1', max_length=1024, blank=True)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('archived', models.BooleanField(default=False)),
                ('notification', models.ForeignKey(related_name='notification_id', to='notifications.Notification')),
                ('user', models.ForeignKey(related_name='user_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
