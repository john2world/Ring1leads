import json
import csv
import os

from django.db import models
from polymorphic import PolymorphicModel, PolymorphicManager
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import CustomUser
from integrations.data import CsvDataSource, PostRunWriter
from integrations.storage import open_s3
from operations.data_processors import EmailEvaluationDataProcessor, AverageAgeEvaluationDataProcessor, \
    LastModifiedAgeEvaluationDataProcessor, GoogleGeocodingDataProcessor, PhoneValidationDataProcessor, \
    CompletenessEvaluationDataProcessor, SpamCheckDataProcessor


class Source(PolymorphicModel):
    user = models.ForeignKey(CustomUser)
    pause_requested = models.BooleanField(default=False)

    def setup_data_source(self, program):
        pass

    def count_records(self, program):
        return 0


class FileSource(Source):
    file = models.FileField()

    def setup_data_source(self, program):
        name = 'program_%s' % program.pk

        data_source = CsvDataSource(name, program)

        data_source.register_processor(EmailEvaluationDataProcessor)
        data_source.register_processor(AverageAgeEvaluationDataProcessor)
        data_source.register_processor(LastModifiedAgeEvaluationDataProcessor)
        data_source.register_processor(GoogleGeocodingDataProcessor)
        data_source.register_processor(PhoneValidationDataProcessor)
        data_source.register_processor(CompletenessEvaluationDataProcessor)
        data_source.register_processor(SpamCheckDataProcessor)

        data_source.register_writer(PostRunWriter, name=name)

        return data_source

    def count_records(self, program):
        if os.path.exists(self.file.url):
            with open(self.file.url, 'rbU') as fp:
                return len(list(csv.DictReader(fp)))

        counter = 0
        if 'amazonaws' in self.file.url:
            fname, ext = os.path.splitext(os.path.basename(self.file.url))

            with open_s3(fname, 'rb') as fp:
                for line in fp:
                    counter += 1
        return counter


# TODO: use django.contrib.postgres.fields.ArrayField for PostgreSQL deployment
class ArrayField(models.TextField):
    """
    Stores a list of strings.
    """

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value == '':
            return None
        elif isinstance(value, basestring):
            #return json.loads(value)
            return value
        return value

    def get_db_prep_save(self, value, *args, **kwargs):
        if value == '':
            return None
        if isinstance(value, list):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return super(ArrayField, self).get_db_prep_save(value, *args, **kwargs)


class ExternalTable(PolymorphicModel):
    """
    A generic database schema, as provided from any of the available data sources.
    """

    name = models.CharField(max_length=512)

    objects = PolymorphicManager()

    def get_field_types(self):
        '''
        Returns a dict matching field labels to field types.
        '''
        types = {}
        for field in self.fields.all():
            types[field.pk] = field.type
        return types

    def get_main_email_field(self):
        '''
        Returns the email field most likely to represent the main contact address
        for the entry, or None if there are no candidates.
        '''
        first_email = None
        for field in self.fields.all():
            if field.get_label().lower() == 'email':
                return field
            if field.get_type() == 'email' and not first_email:
                first_email = field
        return first_email

    def __unicode__(self):
        return u'%s' % self.name


class ExternalField(PolymorphicModel):
    """
    The base class that contains the definition of a database field, to be
    inherited by integrations providing data sources.
    """

    table = models.ForeignKey(ExternalTable, related_name='fields')

    objects = PolymorphicManager()

    def get_label(self):
        """
        Returns the human-friendly name of this field.
        """
        raise NotImplementedError

    def get_name(self):
        """
        Returns the identifier of this field.
        """
        raise NotImplementedError

    def get_type(self):
        """
        Returns the type of this field. May be one of:
          * string
          * boolean
          * int
          * double
          * date
          * datetime
          * binary
          * id
          * reference
          * currency
          * percent
          * phone
          * url
          * email
          * picklist
          * multipicklist
          * anyType
          * location
        """
        raise NotImplementedError

