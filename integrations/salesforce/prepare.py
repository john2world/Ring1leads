"""
Prepares some data pulled from Salesforce prior to passing to qscore.calculate
or other functions that rely on columns and row values being formatted in a
specific way.
"""

import datetime
import numpy as np

import pandas as pd
from pandas import Timestamp
from salesforce_bulk import CsvDictsAdapter
from accounts.models import CustomUser
from integrations import salesforce

from rl_proto2.settings import BASE_DIR
from field_mapper import mapper

import auth


def read_csv(csv_file, program=None):
    csv_df = pd.read_csv(csv_file)

    if program is not None:
        # get date fields (even those mapped by the user)
        for date_field in mapper.date_fields(program):
            if date_field in csv_df:
                csv_df[date_field] = pd.to_datetime(csv_df[date_field])

    # Add a new column and set every row to current date & time
    now = datetime.datetime.now()
    csv_df['now'] = Timestamp(now)
    return csv_df


def get_test_data():
    temp = BASE_DIR + '/temp/report_short.csv'
    return read_csv(temp)


def remove_extra_columns(series):
    """
    Takes a Pandas Series and removes system-generated fields and our own
    fields.  Prerequisite for measurement and ansalysis type functions.
    """
    trimmed = series.drop(
        ['Create Date', 'Last Modified', 'Lead Owner', 'now', 'age'],
        errors='ignore'
    )

    return trimmed


def remove_extra_columns_from_dict(d):
    for field_name in ['Create Date', 'Last Modified', 'Lead Owner', 'now', 'age']:
        if field_name in d:
            del d[field_name]


# https://ap2.salesforce.com/p/setup/layout/LayoutFieldList?type=Lead&setupid=LeadFields
def import_csv_to_sf(csv_path, email, sf_object_name='Lead', count=0, repeat=1):
    """
    Gets OauthToken for user with specified email, maps values from the data frame
    to SF object's schema with sf_object_name.
    """
    user = CustomUser.objects.get(email=email)

    token = salesforce.models.OauthToken.objects.get(user=user)
    token.refresh()

    from integrations.salesforce.models import SalesforceSource
    sf_source, sf_source_created = SalesforceSource.objects.get_or_create(token=token, user=user)
    sf_source.update_schema()

    table_schema = sf_source.salesforce_tables.get(name=sf_object_name)

    bulk = auth.get_prod_auth_for_bulk(token)

    job = bulk.create_insert_job(sf_object_name, contentType='CSV')

    data = read_csv(csv_path)

    row_count = len(data)
    if count != 0:
        row_count = min(len(data), count)

    for i in range(repeat):
        records = []

        for idx in xrange(row_count):
            record = {}

            for field in table_schema.fields.all():
                data_loc = data.loc[idx]

                field_value = data_loc.get(field.name)

                if not field_value:
                    field_value = data_loc.get(field.label) or ''

                if isinstance(field_value, float) and np.isnan(field_value):
                    field_value = ''

                record[field.name] = field_value

            records.append(record)

        csv_iter = CsvDictsAdapter(iter(records))
        batch = bulk.post_bulk_batch(job, csv_iter)
        bulk.wait_for_batch(job, batch)

    bulk.close_job(job)

    # TODO: need to find a way of knowing how many records have failed
    print str(row_count * repeat) + " records are pushed successfully."


# set test_data variable for use in various tests
test_df = get_test_data()
