import os.path

from django.test import TestCase
from django.conf import settings

from model_mommy import mommy

from program_manager.models import Program
from field_mapper.models import MappedField

from . import mapper
from . import exceptions
from . import utils


class FieldMapperTestCase(TestCase):
    def test_fieldlist(self):
        fields = mapper.FieldList(['foo', 'Bar'])

        self.assertIn('foo', fields)
        self.assertIn('bar', fields)

    def test_list_of_mapped_fields(self):
        """ Map field `Country_ex` and `Country_ex2` to `Country`.
        """
        program = mommy.make(Program)

        MappedField.objects.create(
            program=program, from_field='Country_ex', to_field='Country')

        MappedField.objects.create(
            program=program, from_field='Country_ex2', to_field='Country')

        fieldmap = mapper.FieldMapper(program)

        self.assertEqual(
            fieldmap.get_map_list('Country'), ['Country_ex', 'Country_ex2'])

    def test_missing_fields(self):
        """ Create a list of fields without the `Country` field.  The
            `mapper.missing_fields` must return it, since it's part of
            `mapper.REQUIRED_FIELDS`.
        """
        program = mommy.make(Program)

        fields = list(mapper.REQUIRED_FIELDS)
        fields.remove('Country')
        fields.append('Not required field')

        field_mapper = mapper.FieldMapper(program)

        lst = field_mapper.missing_fields(fields)
        self.assertEqual(lst, ['Country'])

    def test_missing_fields_insensitive(self):
        """ Create a list of fields without the `Country` field.
        """
        program = mommy.make(Program)

        fields = list(mapper.REQUIRED_FIELDS)
        fields.remove('Country')
        fields.append('country')

        field_mapper = mapper.FieldMapper(program)

        lst = field_mapper.missing_fields(fields)
        self.assertEqual(lst, [])

    def test_missingfields_exception(self):
        """ Check if the exception is triggered when there are required fields
            missing in a list
        """
        program = mommy.make(Program)

        fields = list(mapper.REQUIRED_FIELDS)
        fields.remove('Country')
        fields.append('Not required field')

        with self.assertRaises(exceptions.MissingFields):
            mapper.check_missing_fields(program, fields)

        fields.append('Country')

        try:
            mapper.check_missing_fields(program, fields)
        except exceptions.MissingFields:
            self.fail('check_missing_fields: should not raise')

    def test_missing_fields_with_user_defined_fields(self):
        """ Create a user-defined mapping for `Country` named `Country_ex`.
            When passing a list containg `Country_ex` to
            `mapper.missing_fields` it must not complain about the missing
            `Country` field, since a mapped field for it exists.
        """
        program = mommy.make(Program)

        MappedField.objects.create(
            program=program, from_field='Country_ex', to_field='Country')

        # test missing field: Country
        fields = list(mapper.REQUIRED_FIELDS)
        fields.remove('Country')

        field_mapper = mapper.FieldMapper(program)

        lst = field_mapper.missing_fields(fields)
        self.assertEqual(lst, ['Country'])

        # test no more missing field: Country
        fields.append('Country_ex')

        lst = field_mapper.missing_fields(fields)

        self.assertEqual(lst, [])

    def test_fieldmapper(self):
        program = mommy.make(Program)

        MappedField.objects.create(
            program=program, from_field='Country_ex', to_field='Country')

        fieldmapper = mapper.FieldMapper(program)

        self.assertEqual(fieldmapper.get_map_list('Country'), ['Country_ex'])
        self.assertEqual(fieldmapper.get_map_list('foo'), [])

    def test_date_fields(self):
        """ When we have a user-defined mapping for a date field, the
            `mapper.date_fields` function must return it instead of the
            source-specific mappings.
        """
        program = mommy.make(Program)

        MappedField.objects.create(program=program, from_field='dtcreated',
                                   to_field='Create Date')

        self.assertEqual(mapper.date_fields(program), [
            'Create Date', 'CreatedDate', 'Last Modified',
            'Last Modified Date', 'LastModifiedDate', 'dtcreated'])

        MappedField.objects.create(program=program, from_field='last_update',
                                   to_field='Last Modified')

        self.assertEqual(mapper.date_fields(program), [
            'Create Date', 'CreatedDate', 'Last Modified',
            'Last Modified Date', 'LastModifiedDate', 'dtcreated',
            'last_update'])


class FieldMapperUtilsTestCase(TestCase):
    def test_valid_csv(self):
        program = mommy.make(Program)
        csv_file = os.path.join(settings.BASE_DIR, 'temp', 'report_short.csv')

        try:
            utils.validate_csv(csv_file, program)
        except exceptions.MissingFields:
            self.fail('test_valid_csv: should not raise exception')

        cols, missing = utils.validate_csv(csv_file, program, ret=True)

        self.assertEqual(missing, [])

    def test_invalid_csv(self):
        program = mommy.make(Program)
        csv_file = os.path.join(
            settings.BASE_DIR, 'temp', 'report_short_missingcols.csv')

        with self.assertRaises(exceptions.MissingFields):
            utils.validate_csv(csv_file, program)

        cols, missing = utils.validate_csv(csv_file, program, ret=True)

        self.assertEqual(missing, ['Create Date', 'Last Modified'])
