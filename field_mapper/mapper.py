import operator

from django.utils.datastructures import SortedDict
from django.db.models import Q

from integrations.salesforce.field_mapping import FIELD_MAPPING as SALESFORCE_MAPPING  # noqa

from . import exceptions


REQUIRED_FIELDS = [
    'Create Date',
    'Last Modified',
    'Phone',
    'Email',
    'Street',
    'City',
    'State/Province',
    'Zip/Postal Code',
    'Country',
]

DATE_FIELDS = [
    'Create Date',
    'Last Modified',
]


class FieldList(list):
    """ List-like class that provides fuzzy comparison. At this moment, it's
        only performing an insensitve-case comparison.
    """
    def __contains__(self, item):
        item = item.lower()

        for f in self:
            if f.lower() == item:
                return True

        return False


class FieldMapper(object):
    """ FieldMapper is used to translate field names, from the standard name
        to mapped name (customized). It does not hold any information about
        the actual list of fields, for this use the FieldList class.
    """
    mapping = SortedDict()
    required_fields = FieldList(REQUIRED_FIELDS)

    def __init__(self, program):
        source_mapping = SALESFORCE_MAPPING

        # walk through hardcoded field names
        for field_to, fields in source_mapping:
            self.mapping[field_to] = fields[0]

        # walk through user-defined field names
        for mapped_field in program.mapped_fields.all():
            field_to = mapped_field.to_field
            self.mapping[mapped_field.from_field] = field_to

    def get_map_list(self, name):
        lst = FieldList()
        for k, v in self.mapping.items():
            if v == name:
                lst.append(k)
        return lst

    def missing_fields(self, fields):
        missing = FieldList()
        fields = FieldList(fields)

        for original_field in self.required_fields:
            if original_field not in fields:
                map_list = self.get_map_list(original_field)
                for mapped_field in map_list:
                    if mapped_field in fields:
                        break
                else:
                    missing.append(original_field)

        return missing


def check_missing_fields(program, lst):
    """ Utility function that raises a MissingFields exception when there are
        required fields missing in `lst`.
    """
    field_mapper = FieldMapper(program)

    missing = field_mapper.missing_fields(FieldList(lst))

    if missing:
        raise exceptions.MissingFields(
            'The following fields are required but not present: {}'.format(
                ', '.join(missing)))


def date_fields(program):
    """ Returns a list containing date fields. The generated list will contain
        those fields defined in `mapper.DATE_FIELDS` and their equivalences
        according to the source being used, except those fields overridden by
        user-defined fields, stored in `field_mapper.models.MappedField`.
    """
    result = []

    date_fields = FieldList(DATE_FIELDS)

    # source-specific mapping
    source_mapping = SALESFORCE_MAPPING

    for to_field, fields in source_mapping:
        if to_field in date_fields:
            result.append(to_field)
            result.extend(fields)

    # user-defined mapping
    Qs = reduce(operator.or_, (Q(to_field__iexact=f) for f in date_fields))

    result.extend(
        program.mapped_fields.filter(Qs).values_list('from_field', flat=True))

    return result
