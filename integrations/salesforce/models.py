from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from simple_salesforce import Salesforce, SalesforceExpiredSession, SalesforceGeneralError

from integrations.data import SalesforceDataSource, DedupeDataProcessor, SalesforceWriter, PostRunWriter
from integrations.salesforce import auth
from integrations.models import ArrayField, ExternalTable, ExternalField
from integrations.salesforce.utils import translate_program_to_soql, \
    count_records
from operations.data_processors import EmailEvaluationDataProcessor, GoogleGeocodingDataProcessor, \
    PhoneValidationDataProcessor, SpamCheckDataProcessor, BroadlookNormalizerDataProcessor
from operations.data_processors import AverageAgeEvaluationDataProcessor
from operations.data_processors import LastModifiedAgeEvaluationDataProcessor
from operations.data_processors import CompletenessEvaluationDataProcessor
from program_manager.models import Source


class OauthToken(models.Model):
    """
    Stores access tokens for Salesforce CRM
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_index=True,
        related_name='oauthtokens',
    )
    salesforce_user_id = models.CharField(
        verbose_name=_('Salesforce User ID'),
        max_length=256,
        null=True,
        blank=True,
    )
    salesforce_organization_id = models.CharField(
        verbose_name=_('Salesforce Org Id'),
        max_length=256,
        null=True,
        blank=True,
    )
    password = models.CharField(    # TODO: This needs to be encrypted!!
        verbose_name=_('Salesforce password'),
        max_length=256,
        null=True,
        blank=True
    )
    instance_url = models.URLField(
        verbose_name=_('Instance URL'),
        null=True,
        blank=True,
    )
    access_token = models.CharField(
        verbose_name=_('Access Token'),
        max_length=256,
        null=True,
        blank=True,
    )
    id_url = models.CharField(
        verbose_name=_('ID URL'),
        max_length=256,
        null=True,
        blank=True,
    )
    id_token = models.CharField(  # TODO: This needs to be encrypted!!
        verbose_name=_('ID Token'),
        max_length=256,
        null=True,
        blank=True,
    )
    refresh_token = models.CharField(  # TODO: This needs to be encrypted!!
        verbose_name=_('Refresh Token'),
        max_length=256,
        null=True,
        blank=True,
    )
    issued_at = models.DateTimeField(
        verbose_name=_('Issued At'),
        null=True,
        blank=True,
    )
    active = models.BooleanField(
        verbose_name=_('Active'),
        default=False,
        db_index=True,
    )
    thumbnail_photo = models.URLField(
        verbose_name=_('Thumbnail Photo'),
        null=True,
        blank=True,
    )
    is_sandbox = models.BooleanField(
        default=False
    )
    # timezone = models.CharField(
    #     max_length=256,
    #     verbose_name=_('Timezone'),
    #     null=True,
    #     blank=True,
    #     )

    def __unicode__(self):
        return str(self.user.email)

    def refresh(self, force=False):
        """
        Refreshes this token if the session has expired.

        :param force: Refresh this token even if the session hasn't expired
        """
        if force:
            auth.refresh_token(self)
            return Salesforce(instance_url=self.instance_url, session_id=self.access_token, sandbox=self.is_sandbox)

        try:
            connection = Salesforce(instance_url=self.instance_url, session_id=self.access_token, sandbox=self.is_sandbox)
            connection.describe()
        except (SalesforceExpiredSession, SalesforceGeneralError):
            auth.refresh_token(self)
            return Salesforce(instance_url=self.instance_url, session_id=self.access_token, sandbox=self.is_sandbox)
        else:
            return connection

    class Meta:
        verbose_name = _('Oauth token')
        verbose_name_plural = _('Oauth tokens')


class SalesforceSource(Source):
    token = models.ForeignKey(OauthToken)

    def setup_data_source(self, program):
        name = 'program_%s' % program.pk
        query = translate_program_to_soql(program)
        updateable = self.salesforce_tables.get(name='Lead').fields.filter(salesforcefield__updateable=True)
        updateable = [f.name for f in updateable]
        data_source = SalesforceDataSource(name, program, token=self.token, query=query, updateable=updateable)

        data_source.register_processor(EmailEvaluationDataProcessor)
        data_source.register_processor(AverageAgeEvaluationDataProcessor)
        data_source.register_processor(LastModifiedAgeEvaluationDataProcessor)
        data_source.register_processor(CompletenessEvaluationDataProcessor)
        data_source.register_processor(GoogleGeocodingDataProcessor)
        data_source.register_processor(PhoneValidationDataProcessor)
        data_source.register_processor(SpamCheckDataProcessor)

        if program.contacts_normalization:
            data_source.register_processor(BroadlookNormalizerDataProcessor)

        # if program.location_optimization:
        #     data_source.register_processor(GoogleGeocodingDataProcessor)

        if program.dedupe:
            data_source.register_processor(DedupeDataProcessor)

        if not program.analyze_only:
            data_source.register_writer(SalesforceWriter, token=self.token, updateable=updateable)

        data_source.register_writer(PostRunWriter, name=name)

        return data_source

    def delete_tables(self):
        for table in SalesforceTable.objects.filter(source=self):
            PicklistValue.objects.filter(schema_field__table=table).delete()
            table.fields.delete()
            table.delete()

    def update_schema(self):
        self.token.refresh()
        self.delete_tables()

        # TODO: load all the tables
        for table_name in ['Lead']:
            self.get_table(table_name)

    def get_table(self, table_name):
        # TODO: validate a table_name?
        table, created = SalesforceTable.objects.get_or_create(name=table_name, source=self)

        if not created:
            return table

        connection = auth.get_prod_auth(self.token)
        connection_table_attr = getattr(connection, table_name)

        if not connection_table_attr:
            raise AttributeError('Table with name %s does not exist' % table_name)

        schema = connection_table_attr.describe()

        for field in schema['fields']:
            # lead_table.fields.create_from_description(field)
            picklist_values = field['picklistValues']
            field['table'] = table
            del field['picklistValues']
            field = SalesforceField.objects.create(**field)
            for picklist in picklist_values:
                field.picklistValues.create(**picklist)

        return table

    def count_records(self, program):
        return count_records(program)


class SalesforceTable(ExternalTable):
    """Describes a table in a Salesforce database."""

    source = models.ForeignKey(SalesforceSource, related_name='salesforce_tables')

    def get_picklist_table(self):
        table = {}
        fields = self.fields.filter(SalesforceField___type='picklist')
        for field in fields:
            table[field.pk] = [(f.value, f.label) for f in field.picklistValues.all()]
        return table


# class SalesforceFieldManager(PolymorphicManager):
#
#    user_for_related_fields = True
#
#    def create_from_description(self, description):
#        """
#        Create a Salesforce field from a description returned from their API.
#        Warning: This call modifies the description.
#        """
#        picklist_values = description['picklistValues']
#        del description['picklistValues']
#        field = self.create(**description)
#        for picklist in picklist_values:
#            field.picklistValues.create(**picklist)
#        return field
#


class SalesforceField(ExternalField):
    """
    Describes a field in a Salesforce table.
    """

    autoNumber = models.BooleanField()
    byteLength = models.PositiveIntegerField()
    calculated = models.BooleanField()
    calculatedFormula = models.TextField(null=True, blank=True)
    cascadeDelete = models.BooleanField()
    caseSensitive = models.BooleanField()
    controllerName = models.CharField(max_length=4096, null=True, blank=True)
    createable = models.BooleanField()
    custom = models.BooleanField()
    defaultValue = models.TextField(null=True, blank=True)
    defaultValueFormula = models.TextField(null=True, blank=True)
    defaultedOnCreate = models.BooleanField()
    dependentPicklist = models.BooleanField()
    deprecatedAndHidden = models.BooleanField()
    digits = models.PositiveIntegerField()
    displayLocationInDecimal = models.BooleanField()
    externalId = models.BooleanField()
    filterable = models.BooleanField()
    groupable = models.BooleanField()
    htmlFormatted = models.BooleanField()
    idLookup = models.BooleanField()
    inlineHelpText = models.TextField(null=True, blank=True)
    label = models.CharField(max_length=1024)
    length = models.PositiveIntegerField()
    name = models.CharField(max_length=1024)
    nameField = models.BooleanField()
    namePointing = models.BooleanField()
    nillable = models.BooleanField()
    permissionable = models.BooleanField()
    # picklistValues - reverse foreign key (PicklistValue)
    precision = models.PositiveSmallIntegerField()
    referenceTo = ArrayField()
    relationshipName = models.CharField(max_length=1024, null=True, blank=True)
    relationshipOrder = models.PositiveSmallIntegerField(null=True, blank=True)
    restrictedDelete = models.BooleanField()
    restrictedPicklist = models.BooleanField()
    scale = models.PositiveIntegerField()
    soapType = models.CharField(max_length=1024)
    sortable = models.BooleanField()
    type = models.CharField(max_length=1024)
    unique = models.BooleanField()
    updateable = models.BooleanField()
    writeRequiresMasterRead = models.BooleanField()

    #objects = SalesforceFieldManager()

    def get_label(self):
        return self.label

    def get_name(self):
        return self.name

    def get_type(self):
        mappings = {
            'base64': 'binary',
            'textarea': 'string',
            'combobox': 'string'}
        return mappings.get(self.type, self.type)

    def __unicode__(self):
        return u'%s' % self.label


class PicklistValue(models.Model):
    """An item in a Salesforce picklist."""
    schema_field = models.ForeignKey(SalesforceField, related_name='picklistValues')
    active = models.BooleanField()
    defaultValue = models.BooleanField()
    label = models.CharField(max_length=512)
    validFor = models.CharField(max_length=64, null=True, blank=True) # TODO: check how the Salesforce API retrieves this field (bitfield)
    value = models.TextField()
