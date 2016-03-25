# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import integrations.models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OauthToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('salesforce_user_id', models.CharField(max_length=256, null=True, verbose_name='Salesforce User ID', blank=True)),
                ('salesforce_organization_id', models.CharField(max_length=256, null=True, verbose_name='Salesforce Org Id', blank=True)),
                ('password', models.CharField(max_length=256, null=True, verbose_name='Salesforce password', blank=True)),
                ('instance_url', models.URLField(null=True, verbose_name='Instance URL', blank=True)),
                ('access_token', models.CharField(max_length=256, null=True, verbose_name='Access Token', blank=True)),
                ('id_url', models.CharField(max_length=256, null=True, verbose_name='ID URL', blank=True)),
                ('id_token', models.CharField(max_length=256, null=True, verbose_name='ID Token', blank=True)),
                ('refresh_token', models.CharField(max_length=256, null=True, verbose_name='Refresh Token', blank=True)),
                ('issued_at', models.DateTimeField(null=True, verbose_name='Issued At', blank=True)),
                ('active', models.BooleanField(default=False, db_index=True, verbose_name='Active')),
                ('thumbnail_photo', models.URLField(null=True, verbose_name='Thumbnail Photo', blank=True)),
                ('is_sandbox', models.BooleanField(default=False)),
                ('user', models.ForeignKey(related_name='oauthtokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Oauth token',
                'verbose_name_plural': 'Oauth tokens',
            },
        ),
        migrations.CreateModel(
            name='PicklistValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField()),
                ('defaultValue', models.BooleanField()),
                ('label', models.CharField(max_length=512)),
                ('validFor', models.CharField(max_length=64, null=True, blank=True)),
                ('value', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SalesforceField',
            fields=[
                ('externalfield_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='integrations.ExternalField')),
                ('autoNumber', models.BooleanField()),
                ('byteLength', models.PositiveIntegerField()),
                ('calculated', models.BooleanField()),
                ('calculatedFormula', models.TextField(null=True, blank=True)),
                ('cascadeDelete', models.BooleanField()),
                ('caseSensitive', models.BooleanField()),
                ('controllerName', models.CharField(max_length=4096, null=True, blank=True)),
                ('createable', models.BooleanField()),
                ('custom', models.BooleanField()),
                ('defaultValue', models.TextField(null=True, blank=True)),
                ('defaultValueFormula', models.TextField(null=True, blank=True)),
                ('defaultedOnCreate', models.BooleanField()),
                ('dependentPicklist', models.BooleanField()),
                ('deprecatedAndHidden', models.BooleanField()),
                ('digits', models.PositiveIntegerField()),
                ('displayLocationInDecimal', models.BooleanField()),
                ('externalId', models.BooleanField()),
                ('filterable', models.BooleanField()),
                ('groupable', models.BooleanField()),
                ('htmlFormatted', models.BooleanField()),
                ('idLookup', models.BooleanField()),
                ('inlineHelpText', models.TextField(null=True, blank=True)),
                ('label', models.CharField(max_length=1024)),
                ('length', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=1024)),
                ('nameField', models.BooleanField()),
                ('namePointing', models.BooleanField()),
                ('nillable', models.BooleanField()),
                ('permissionable', models.BooleanField()),
                ('precision', models.PositiveSmallIntegerField()),
                ('referenceTo', integrations.models.ArrayField()),
                ('relationshipName', models.CharField(max_length=1024, null=True, blank=True)),
                ('relationshipOrder', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('restrictedDelete', models.BooleanField()),
                ('restrictedPicklist', models.BooleanField()),
                ('scale', models.PositiveIntegerField()),
                ('soapType', models.CharField(max_length=1024)),
                ('sortable', models.BooleanField()),
                ('type', models.CharField(max_length=1024)),
                ('unique', models.BooleanField()),
                ('updateable', models.BooleanField()),
                ('writeRequiresMasterRead', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('integrations.externalfield',),
        ),
        migrations.CreateModel(
            name='SalesforceSource',
            fields=[
                ('source_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='integrations.Source')),
                ('token', models.ForeignKey(to='salesforce.OauthToken')),
            ],
            options={
                'abstract': False,
            },
            bases=('integrations.source',),
        ),
        migrations.CreateModel(
            name='SalesforceTable',
            fields=[
                ('externaltable_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='integrations.ExternalTable')),
                ('source', models.ForeignKey(related_name='salesforce_tables', to='salesforce.SalesforceSource')),
            ],
            options={
                'abstract': False,
            },
            bases=('integrations.externaltable',),
        ),
        migrations.AddField(
            model_name='picklistvalue',
            name='schema_field',
            field=models.ForeignKey(related_name='picklistValues', to='salesforce.SalesforceField'),
        ),
    ]
