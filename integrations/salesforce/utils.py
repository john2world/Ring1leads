import re
import time
import math
import urlparse
from pip._vendor.requests import RequestException
import requests
import cStringIO as StringIO
from simple_salesforce import (
    Salesforce,
    SalesforceExpiredSession,
    SalesforceRefusedRequest,
    SalesforceError)
import xml.etree.ElementTree as ET
from program_manager.choices import *
from salesforce_bulk import SalesforceBulk
from program_manager.utils import django_model_instance_to_dict


class BulkApiError(Exception):

    def __init__(self, message, status_code=None):
        super(BulkApiError, self).__init__(message)
        self.status_code = status_code


class CustomSalesforceBulk(SalesforceBulk):

    def __init__(self, is_sandbox=False, *args, **kwargs):
        super(CustomSalesforceBulk, self).__init__(*args, **kwargs)
        self.host = kwargs.get('host', None)
        self.is_sandbox = is_sandbox
        self.chunk_size = 100000
        self.downloaded = 0
        self.posted = 0

    def headers(self, values={}):
        result = super(CustomSalesforceBulk, self).headers(values)
        result['Sforce-Enable-PKChunking'] = 'chunkSize=%s;' % self.chunk_size
        return result

    def job_batches_status(self, job_id):
        uri = urlparse.urljoin(self.endpoint +"/", 'job/{0}/batch'.format(job_id))
        response = requests.get(uri, headers=self.headers())
        if response.status_code != 200:
            self.raise_error(response.content, response.status_code)
        tree = ET.fromstring(response.content)
        result = []
        for child in tree:
            batch = {}
            for prop in child:
                batch[re.sub(r'{.*?}', '', prop.tag)] = prop.text
            result.append(batch)
        return result

    def get_connection(self):
        return Salesforce(instance_url=self.host, session_id=self.sessionId,
                          sandbox=self.is_sandbox)

    def count_records(self, connection, query):
        return connection.query(query)['totalSize']

    def download_database(self, connection, query):
        print query
        count = self.count_records(connection, query)
        print '%s records match. Starting download process...' % count
        self.chunk_size = int(max(5000, count / 100))
        print 'Chunk size set to %s.' % self.chunk_size
        for chunk in self.process_SOQL_with_auth(query, expected=int(math.ceil(count / self.chunk_size))):
            yield chunk

    def get_batch_results_fast(self, batch_id, result_id, job_id):
        uri = urlparse.urljoin(
            self.endpoint + "/",
            "job/{0}/batch/{1}/result/{2}".format(
                job_id, batch_id, result_id),
        )
        resp = requests.get(uri, headers=self.headers())
        self.downloaded += len(resp.content)
        return resp.content

    def process_SOQL_with_auth(self, query, table="Lead", expected=0, export_name=''):
        """ Takes a SOQL query and a specified table and returns a DictReader
        object. """
        print "Processing SOQL with Salesforce authentication."
        job = self.create_query_job(table, contentType='CSV')
        batch = self.query(job, query)
        #self.close_job(job) # don't. this will prevent autochunking from working.
        # wait for Salesfoce to begin generating the chunked batches
        while len(self.job_batches_status(job)) < 2:
            print 'Waiting for autochunking to begin...'
            print self.job_status(job)
            print self.batch_status(job, batch, reload=True)
            time.sleep(5)
        # wait until all batches are finished, downloading them as they do so
        uploaded_batches = []
        first = True
        while True:
            completed = 0
            batches = self.job_batches_status(job)
            num_batches = len(batches) - 1
            for batch in batches:
                if batch['state'] == 'Completed':
                    if not batch['id'] in uploaded_batches:
                        # if this batch hasn't been procesed, export it
                        result = self.download_batch(job, batch['id'])
                        uploaded_batches.append(batch['id'])
                        print 'Finished %s out of %s batches (%s expected)' % (completed, num_batches, expected)
                        if first:
                            first = False
                        else:
                            result = self.strip_header_buffer(result)
                        if len(result):
                            yield result
                    completed += 1
            if completed == num_batches:
                # FIXME: make sure we don't outrun the autochunker
                break

    def download_batch(self, job, batch):
        print 'Processing batch %s.' % batch
        data = ''
        result_ids = self.get_batch_result_ids(batch_id=batch, job_id=job)
        first = True
        for result_id in result_ids:
            print 'Downloading results (%s MB downloaded so far).' % (self.downloaded / (1024 * 1024))
            new_data = self.get_batch_results_fast(batch, result_id, job)
            if first:
                data += new_data
            else:
                data += self.strip_header_buffer(new_data)
            first = False
        return data

    def strip_header_buffer(self, data):
        return memoryview(data)[data.find('\n'):]


class InvalidSalesforceQueryCondition(Exception):
    pass


class SalesforceQueryBuilder(object):
    OPERATOR_TYPE_TEXT = 'TEXT'
    OPERATOR_TYPE_NUM = 'NUM'
    OPERATOR_TYPE_DATETIME = 'DATETIME'
    OPERATOR_TYPE_BOOL = 'BOOL'
    OPERATOR_TYPE_MATCH = 'MATCH'

    OPERATOR_TYPES = {
        OPERATOR_TYPE_TEXT: TEXT_OPERATORS,
        OPERATOR_TYPE_NUM: NUM_OPERATORS,
        OPERATOR_TYPE_DATETIME: DATETIME_OPERATORS,
        OPERATOR_TYPE_BOOL: BOOL_OPERATORS,
        OPERATOR_TYPE_MATCH: MATCH_OPERATORS
    }

    OPERATORS_MAP = {
        TEXT_EQUALS: ('=', lambda val: "'%s'" % val),
        TEXT_NOT_EQUALS: ('!=', lambda val: "'%s'" % val),
        TEXT_CONTAINS: ('LIKE', lambda val: "'%%%s%%'" % val),
        TEXT_STARTS: ('LIKE', lambda val: "'%s%%'" % val),
        NUM_EQUALS: ('=', lambda val: '%s' % val),
        NUM_GREATER: ('>', lambda val: '%s' % val),
        NUM_LESS: ('<', lambda val: '%s' % val),
        DATETIME_EQUALS: ('=', lambda val:  '%s' % val),
        DATETIME_AFTER: ('>', lambda val:  '%s' % val),
        DATETIME_BEFORE: ('<', lambda val: '%s' % val),
        BOOL_TRUE: ('=', lambda val:  'TRUE'),
        BOOL_FALSE: ('=', lambda val: 'FALSE'),
    }

    def __init__(self, program, schema_name, *args, **kwargs):
        self.program = program
        self.schema_name = schema_name
        self.fields = program.source.salesforce_tables.get(name=schema_name).fields.all()
        self.fields_names = [field.get_name() for field in self.fields]
        self.filters = program.fieldfilter_set.all()

    def get_operator_type(self, operator, default=OPERATOR_TYPE_TEXT):
        for operator_type, operators in self.OPERATOR_TYPES.iteritems():
            if operator in dict(operators).keys():
                return operator_type
        return default

    @staticmethod
    def validate_field_filter(field, operator, field_value):
        """
        Checks if filter's value and operator are applicable to its field.
        Otherwise raises InvalidSalesforceQueryCondition.
        """
        bool_ops, bool_ops_names = zip(*BOOL_OPERATORS)
        num_ops, num_ops_names = zip(*NUM_OPERATORS)
        date_ops, date_ops_names = zip(*DATETIME_OPERATORS)

        if operator in bool_ops:
            return

        if not field_value:
            raise InvalidSalesforceQueryCondition('Empty values are not allowed.')

        if operator in num_ops:
            try:
                float(field_value)
            except ValueError:
                raise InvalidSalesforceQueryCondition('%s operator requires a numeric value.' % operator)

        if operator in date_ops:
            try:
                from program_manager.forms import natural_date_parse
                natural_date_parse(field_value)
            except ValueError:
                raise InvalidSalesforceQueryCondition('%s operator requires a datetime value.' % operator)

        if field.type in ['id', 'reference']:
            if operator == TEXT_EQUALS:
                if len(field_value) != 15 and len(field_value) != 18:
                    raise InvalidSalesforceQueryCondition('Salesforce ID should contain 15 or 18 characters.')

            if operator in [TEXT_CONTAINS, TEXT_STARTS]:
                raise InvalidSalesforceQueryCondition('Invalid operator type for ID field.')

    def make_where_clause(self, field_filter):
        field = field_filter.field
        operator = field_filter.operator
        field_value = field_filter.field_value

        self.validate_field_filter(field, operator, field_value)

        if ',' in field_value:
            field_value = '(%s)' % ' OR '.join(
                [self.OPERATORS_MAP[operator][1](v.strip()) for v in field_value.split(',')])
        else:
            field_value = self.OPERATORS_MAP[operator][1](field_value)

        clause_format_string = "%s %s '%s'"

        if self.get_operator_type(operator) == self.OPERATOR_TYPE_DATETIME \
                or self.get_operator_type(operator) == self.OPERATOR_TYPE_BOOL:
            clause_format_string = "%s %s %s"

        return clause_format_string % (field.name, self.OPERATORS_MAP[operator][0], field_value.replace("'", ""))

    def get_query(self, count_only=False):
        """
        :return: Saleforce Query as strings
        """
        wheres = []
        for field_filter in self.filters:
            wheres.append(self.make_where_clause(field_filter))
        if count_only:
            selects = 'count()'
        else:
            selects = ', '.join(self.fields_names)
        if wheres:
            return 'SELECT %s FROM %s WHERE %s' % (selects, self.schema_name, ' AND '.join(wheres))
        else:
            return 'SELECT %s FROM %s' % (selects, self.schema_name)


def translate_program_to_soql(program, count_only=False):
    """ Build complete SOQL statement to retrieve all possible fields and
     applying all related FieldFilters."""
    parser = SalesforceQueryBuilder(program, 'Lead')
    return parser.get_query(count_only=count_only)


def count_records(program):
    query = translate_program_to_soql(program, count_only=True)

    # fetch count
    program.source.token.refresh()  # TODO: Source.count_records
    conn = Salesforce(session_id=program.source.token.access_token,
                      instance_url=program.source.token.instance_url,
                      sandbox=program.source.token.is_sandbox)

    try:
        count = conn.query(query)['totalSize']
    except SalesforceError as e:
        raise Exception({
            'type': 'salesforceerror',
            'data': e.content[0],
        })
    except RequestException:
        raise Exception({
            'type': 'connectionerror',
        })
    except:
        raise Exception({
            'type': 'unknown',
        })
    else:
        return count
