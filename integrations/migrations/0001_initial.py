# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_integrations.externalfield_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExternalTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=512)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_integrations.externaltable_set+', editable=False, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FileSource',
            fields=[
                ('source_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='integrations.Source')),
                ('file', models.FileField(upload_to=b'')),
            ],
            options={
                'abstract': False,
            },
            bases=('integrations.source',),
        ),
        migrations.AddField(
            model_name='source',
            name='polymorphic_ctype',
            field=models.ForeignKey(related_name='polymorphic_integrations.source_set+', editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='source',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='externalfield',
            name='table',
            field=models.ForeignKey(related_name='fields', to='integrations.ExternalTable'),
        ),
    ]
