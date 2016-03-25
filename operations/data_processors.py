import collections
from itertools import izip
import datetime
import operator
import pandas as pd
from requests.exceptions import ConnectTimeout
from integrations.data import DataProcessor, BatchDataProcessor
from integrations.salesforce.prepare import remove_extra_columns_from_dict
from operations.email_query import get_is_spam_record, get_is_email_valid
from operations.exceptions import InsufficientCreditsError
from operations.location_validators import GeocodeValidator, ValidationException
from operations.normalizer import ContactsNormalizer
from operations.phone_query import get_country_code
from operations.phone_validators import ValidatorServiceError, TwilioValidator
from program_manager.choices import UPDATE_POLICY_CHOICES
from qscore.utils import LocationBuilder

SideScore = collections.namedtuple('SideScore', ['limit', 'point', 'operator'])
RangeScore = collections.namedtuple('ScoreRange', ['lower', 'upper', 'point'])

location_validator = GeocodeValidator()
twilio_validator = TwilioValidator()


class GoogleGeocodingDataProcessor(DataProcessor):
    """
    Queries Google Geocoding API.

    As of now, this processor is used only for quality score calculations due to its slow perfomance (no bulk queries).
    To enable it for location optimization - uncomment receive_row, final portion of _process_row,
    and also enable analyze mode check in get_qscore_value.
    """

    ACTIVITY_DESCRIPTION = 'Optimizing location and address data.'

    DEFAULT_SAMPLE_SIZE = 50

    SCORE_RANGES = {
        'name': 'percent_valid_location',
        'left': SideScore(90, 10, operator.ge),
        'right': SideScore(59, 0, operator.le),
        'ranges': [RangeScore(80, 89, 8), RangeScore(70, 79, 5), RangeScore(60, 69, 2)],
    }

    TEMP_MAPPING = {
        'Street': 'street',
        'City': 'city',
        'State': 'state',
        'PostalCode': 'zipcode',
        'Country': 'country',
    }

    def __init__(self, *args, **kwargs):
        super(GoogleGeocodingDataProcessor, self).__init__(*args, **kwargs)
        self.rules = []
        self.valid_count = 0
        self.eligible_rows_count = 0

    # ATTENTION: if you're going to remove these lines, make sure you've read docstring first.
    # def receive_row(self, row):
    #     if self.source.program.analyze_only:
    #         return row  # will take sample in get_qscore_value in that case
    #
    #     return self._process_row(row)

    def _process_row(self, row):
        location = self._build_location(row)

        if not location:
            return row

        self.eligible_rows_count += 1

        try:
            result = location_validator.validate(location)
        except InsufficientCreditsError:
            return row
        except (ValueError, ValidationException):
            result = dict(valid=False)

        if not result.get('valid', False):
            return row

        self.valid_count += 1

        # values = result.get('valid_address', {})
        #
        # if not self.source.program.analyze_only:
        #     row = self._process_result_values(row, values)
        #     self.mark_for_write(row)

        return row

    def _process_result_values(self, row, values):
        self.rules = list(self.source.program.location_optimization_rules.all())

        for field_name, google_name in self.TEMP_MAPPING.iteritems():
            processed_field_value = values.get(google_name, None)

            if processed_field_value:
                field_value = unicode(row.get(field_name, ''))
                processed_field_value = unicode(processed_field_value)

                row[field_name] = self._apply_rule(field_name, field_value, processed_field_value)

        return row

    def _build_location(self, row):
        location = {}

        for field_name, google_name in self.TEMP_MAPPING.iteritems():
            location[google_name] = row.get(field_name, '')

        return LocationBuilder(location)

    def _apply_rule(self, field_name, field_value, processed_field_value):
        rule = self._get_rule(field_name)

        if rule == UPDATE_POLICY_CHOICES[0][0]:  # OVERWRITE
            return processed_field_value

        elif rule == UPDATE_POLICY_CHOICES[1][0] and not field_value:  # UPDATE_IF_BLANK
            return processed_field_value

        elif rule == UPDATE_POLICY_CHOICES[2][0]:  # DO_NOT_UPDATE
            return field_value

        return processed_field_value

    def _get_rule(self, field_name):
        return next((rule.rule for rule in self.rules if rule.field.get_name() == field_name), UPDATE_POLICY_CHOICES[0][0])

    def get_qscore_value(self):
        # if self.source.program.analyze_only:
        random_ids = self.get_random_ids()

        for random_id in random_ids:
            row = self.load(random_id)
            self._process_row(row)

        if not self.eligible_rows_count:
            return None

        percent_valid = self.valid_count * 100 / self.eligible_rows_count
        # print 'VALID LOCATIONS PERCENT: {0}'.format(percent_valid)
        return percent_valid


class BroadlookNormalizerDataProcessor(BatchDataProcessor):

    ACTIVITY_DESCRIPTION = 'Normalizing contacts data.'

    TEMP_MAPPING = {  # TODO: this mapping is TEMP, it works only for SF's Lead table, we need a mapping solution
        'Company': 'CompanyName',
        'City': 'City',
        'Street': 'StreetLine',
        'State': 'StateProvince',
        'Phone': 'USPhone',
        'Website': 'URL',
        'Title': 'JobTitle'
    }  # TODO: properly handle Name field, broadlook expects a concatenated name (first+middle+surname)

    INVERSE_MAPPING = {v: k for k, v in TEMP_MAPPING.iteritems()}

    def __init__(self, *args, **kwargs):
        super(BroadlookNormalizerDataProcessor, self).__init__(*args, **kwargs)
        self.rules = list(self.source.program.contacts_normalizer_rules.exclude(rule='None'))
        self.normalizer_settings = self.setup_normalizer_settings()
        self.normalizer = ContactsNormalizer(settings=self.normalizer_settings)

    def setup_normalizer_settings(self):
        normalizer_settings = {}

        for rule in self.rules:
            normalizer_settings[rule.api_field_name] = rule.rule

        return normalizer_settings

    def process_batch(self):
        if not self.current_batch_len:
            return

        mapped_batch = [self._map_to_broadlook_fields(row) for row in self.current_batch]
        status_code, normalized_contacts = self.normalizer.normalize(mapped_batch)

        if status_code != 200:
            return

        for row, normalized_contact in izip(self.current_batch, normalized_contacts):
            self._update_row(row, normalized_contact)

    def _map_to_broadlook_fields(self, row):
        result_row = {'_RecordID': row['_id']}

        for k, v in row.iteritems():
            if k in self.TEMP_MAPPING and v:
                broadlook_field_name = self.TEMP_MAPPING[k]
                result_row[broadlook_field_name] = v

        return result_row

    def _update_row(self, row, result_dict):
        if not result_dict:
            return

        updated = False
        for k, v in result_dict.iteritems():
            if not v or v == '[NOT PROVIDED]' or k not in self.INVERSE_MAPPING:
                continue

            schema_field_name = self.INVERSE_MAPPING[k]

            if v == row[schema_field_name]:
                continue

            row[schema_field_name] = v
            updated = True

        if updated:
            row['_normalized'] = True
            self.save(row)


class SpamCheckDataProcessor(DataProcessor):

    ACTIVITY_DESCRIPTION = 'Searching for SPAM records.'

    SCORE_RANGES = {
        'name': 'percent_spam_email',
        'left': SideScore(5, 10, operator.le),
        'right': SideScore(12, 0, operator.ge),
        'ranges': [RangeScore(5, 7, 8), RangeScore(7, 9, 5), RangeScore(9, 12, 2)],
    }

    def __init__(self, *args, **kwargs):
        super(SpamCheckDataProcessor, self).__init__(*args, **kwargs)
        self.valid_count = 0
        self.spam_count = 0
        self.eligible_rows_count = 0

    def receive_row(self, row):
        email = row.get('Email')

        if not email:
            return row

        self.eligible_rows_count += 1

        spam_check_result = get_is_spam_record(row, email)

        # print 'RECORD #{0} IS SPAM: {1}'.format(row['_id'], spam_check_result.get('spam', False))

        if not spam_check_result.get('spam', False):
            self.valid_count += 1
            return row

        self.spam_count += 1

        if not self.source.program.analyze_only and self.source.program.junk_removal_settings.delete_spam_records:
            self.mark_for_deletion(row)

        return row

    def get_qscore_value(self):
        if not self.eligible_rows_count:
            return None

        spam_percent = float(self.spam_count * 100) / self.eligible_rows_count
        # print 'SPAM RECORDS PERCENT: {0}'.format(spam_percent)
        return spam_percent


class CompletenessEvaluationDataProcessor(DataProcessor):

    ACTIVITY_DESCRIPTION = 'Scoring records\' completeness.'

    SCORE_RANGES = {
        'name': 'percent_complete',
        'left': SideScore(90, 10, operator.ge),
        'right': SideScore(59, 0, operator.le),
        'ranges': [RangeScore(80, 89, 8), RangeScore(70, 79, 5), RangeScore(60, 69, 2)],
    }

    def __init__(self, *args, **kwargs):
        super(CompletenessEvaluationDataProcessor, self).__init__(*args, **kwargs)
        self.percent_buffer = 0
        self.eligible_rows_count = 0

    def receive_row(self, row):
        self.eligible_rows_count += 1

        temp_row = row.copy()

        self.source.remove_metadata(temp_row)
        remove_extra_columns_from_dict(temp_row)

        columns_count = len(temp_row)
        filled_count = 0

        for k, v in temp_row.iteritems():
            if v:
                filled_count += 1

        percent_filled = filled_count * 100 / columns_count

        self.percent_buffer += percent_filled

        return row

    def get_qscore_value(self):
        if not self.eligible_rows_count:
            return None
        avg = self.percent_buffer / self.eligible_rows_count
        # print 'CALCULATED COMPLETENESS PERCENT: {0}'.format(avg)
        return avg


class AverageAgeEvaluationDataProcessor(DataProcessor):

    ACTIVITY_DESCRIPTION = 'Calculating an average age of your records.'

    SCORE_RANGES = {
        'name': 'avg_age',
        'left': SideScore(45, 10, operator.le),
        'right': SideScore(360, 0, operator.ge),
        'ranges': [RangeScore(46, 90, 8), RangeScore(91, 180, 5), RangeScore(181, 359, 2)],
    }

    def __init__(self, *args, **kwargs):
        super(AverageAgeEvaluationDataProcessor, self).__init__(*args, **kwargs)
        self.now = datetime.datetime.now()
        self.days_delta_buffer = 0
        self.eligible_rows_count = 0

    def receive_row(self, row):
        created_date_string = row.get('Create Date') or row.get('CreatedDate')

        if not created_date_string:
            return row

        created_date_datetime = pd.to_datetime(created_date_string)

        try:
            self.days_delta_buffer += (self.now - created_date_datetime).days
            self.eligible_rows_count += 1
        except:
            pass

        return row

    def get_qscore_value(self):
        if not self.eligible_rows_count:
            return None
        avg = self.days_delta_buffer / self.eligible_rows_count
        # print 'AVERAGE RECORD AGE: {0}'.format(avg)
        return avg


class LastModifiedAgeEvaluationDataProcessor(DataProcessor):

    ACTIVITY_DESCRIPTION = 'Calculating an average time since the records were modified.'

    SCORE_RANGES = {
        'name': 'avg_since_last_modified',
        'left': SideScore(30, 10, operator.le),  # if average <= 30, then return 10 score
        'right': SideScore(91, 0, operator.ge),  # if average >= 91, then return 0 score
        'ranges': [RangeScore(31, 45, 8), RangeScore(46, 60, 5), RangeScore(61, 90, 2)],
    }

    def __init__(self, *args, **kwargs):
        super(LastModifiedAgeEvaluationDataProcessor, self).__init__(*args, **kwargs)
        self.now = datetime.datetime.now()
        self.days_delta_buffer = 0
        self.eligible_rows_count = 0

    def receive_row(self, row):
        last_modified_date_string = row.get('Last Modified') or row.get('LastModifiedDate')

        if not last_modified_date_string:
            return row

        last_modified_date_datetime = pd.to_datetime(last_modified_date_string)

        try:
            self.days_delta_buffer += (self.now - last_modified_date_datetime).days
            self.eligible_rows_count += 1
        except:
            pass

        return row

    def get_qscore_value(self):
        if not self.eligible_rows_count:
            return None
        avg = self.days_delta_buffer / self.eligible_rows_count
        # print 'AVERAGE LAST MODIFIED AGE: {0}'.format(avg)
        return avg


class PhoneValidationDataProcessor(DataProcessor):

    ACTIVITY_DESCRIPTION = 'Optimizing phones data.'

    DEFAULT_SAMPLE_SIZE = 1000

    SCORE_RANGES = {
        'name': 'percent_valid_phone',
        'left': SideScore(90, 10, operator.ge),
        'right': SideScore(59, 0, operator.le),
        'ranges': [RangeScore(80, 89, 8), RangeScore(70, 79, 5), RangeScore(60, 69, 2)],
    }

    def __init__(self, *args, **kwargs):
        super(PhoneValidationDataProcessor, self).__init__(*args, **kwargs)
        self.valid_count = 0
        self.invalid_count = 0
        self.eligible_rows_count = 0

    def get_qscore_value(self):
        random_ids = self.get_random_ids()

        for random_id in random_ids:
            row = self.load(random_id)

            phone = row.get('Phone')

            if not phone:
                continue

            country = row.get('Country')

            if isinstance(country, basestring):
                country_code = get_country_code(country)
            else:
                country_code = ''

            try:
                result = twilio_validator.validate(phone, extra=False, country=country_code)
            except ValidatorServiceError:
                break
            except ConnectTimeout:
                continue

            self.eligible_rows_count += 1

            if not result.get('valid', False):
                self.invalid_count += 1
            else:
                self.valid_count += 1

        if not self.eligible_rows_count:
            return None

        avg = self.valid_count * 100 / self.eligible_rows_count
        # print 'PERCENT OF VALID PHONES: {0}'.format(avg)
        return avg


class EmailEvaluationDataProcessor(DataProcessor):

    ACTIVITY_DESCRIPTION = 'Validating emails.'

    SCORE_RANGES = {
        'name': 'percent_valid_email',
        'left': SideScore(90, 10, operator.ge),
        'right': SideScore(59, 0, operator.le),
        'ranges': [RangeScore(80, 89, 8), RangeScore(70, 79, 5), RangeScore(60, 69, 2)],
    }

    def __init__(self, *args, **kwargs):
        super(EmailEvaluationDataProcessor, self).__init__(*args, **kwargs)
        self.valid_count = 0
        self.invalid_count = 0
        self.eligible_rows_count = 0

    def receive_row(self, row):
        email = row.get('Email')

        if not email:
            return row

        self.eligible_rows_count += 1

        if not get_is_email_valid(email):
            self.invalid_count += 1
            return row

        self.valid_count += 1

        return row

    def get_qscore_value(self):
        if not self.eligible_rows_count:
            return None

        avg = self.valid_count * 100 / self.eligible_rows_count
        # print 'PERCENT OF VALID EMAILS: {0}'.format(avg)
        return avg
