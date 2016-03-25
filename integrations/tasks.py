from __future__ import absolute_import

import io
import csv
import boto
import codecs
import cStringIO
import smart_open
from boto.s3.key import Key
from celery import shared_task
from django.conf import settings
from program_manager.models import Program
from program_manager.tasks import JobTask
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(base=JobTask)
def export_csv(program_pk, data):
    program = Program.objects.get(pk=program_pk)
    logger.info('Starting S3 .csv backup export...')
    connection = boto.connect_s3(settings.AWS_ACCESS_KEY_ID,
                                 settings.AWS_SECRET_ACCESS_KEY)
    bucket = connection.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    key = Key(bucket)
    key.key = 'backup-%s' % program_pk
    with smart_open.smart_open(key, 'wb') as s3_file:
        writer = csv.writer(s3_file)
        for row in data:
            writer.writerow([r.decode('utf-8').encode('utf-8') for r in row])
    key.set_acl('public-read')
    program.pre_backup_url = key.generate_url(expires_in=0, query_auth=False)
    print program.pre_backup_url
    program.save()
    logger.info('Finished S3 .csv backup export...')


@shared_task
def execute_query(s_instance, job, result_id, batch, parse_csv):
    for row in s_instance.get_batch_results(job_id=job, result_id=result_id, batch_id=batch, parse_csv=parse_csv):
        field_name = row
        break

    file = io.StringIO()

    # bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    # conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    # bucket = conn.get_bucket(bucket_name)

    s3_link = "s3://" + settings.AWS_ACCESS_KEY_ID + ":" + settings.AWS_SECRET_ACCESS_KEY + "@" + settings.AWS_STORAGE_BUCKET_NAME + "/csv_stream/first.csv"
    with smart_open.smart_open(s3_link, 'wb') as fout:
        writer = UnicodeDictWriter(file, fieldnames=field_name)

        writer.writeheader()
        fout.write(file.getvalue())

        for row in s_instance.get_batch_results(job_id=job, result_id=result_id, batch_id=batch, parse_csv=True):
            value = dict()

            for i in range(0, len(field_name), 1):
                field = field_name[i]
                value.update({field: row[i]})
            file.seek(0)
            file.truncate(0)
            writer.writerow(value)
            fout.write(file.getvalue())

    file.close()


def extract_csv(batch_name):
    s3_link = "s3://" + settings.AWS_ACCESS_KEY_ID + ":" + settings.AWS_SECRET_ACCESS_KEY + "@" + settings.AWS_STORAGE_BUCKET_NAME + "/csv_stream/final.csv"
    return smart_open.smart_open(s3_link)


def update_csv(fieldnames, data_dict):
    file = io.StringIO()

    s3_link = "s3://" + settings.AWS_ACCESS_KEY_ID + ":" + settings.AWS_SECRET_ACCESS_KEY + "@" + settings.AWS_STORAGE_BUCKET_NAME + "/csv_stream/final.csv"
    with smart_open.smart_open(s3_link, 'wb') as fout:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        fout.write(file.getvalue())

        for row in data_dict:
            file.seek(0)
            file.truncate(0)
            writer.writerow(row)
            fout.write(file.getvalue())

    file.close()


class UTF8Recoder:
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)
    def __iter__(self):
        return self
    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8-sig", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)
    def next(self):
        '''next() -> unicode
        This function reads and returns the next line as a Unicode string.
        '''
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]
    def __iter__(self):
        return self


class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        '''writerow(unicode) -> None
        This function takes a Unicode string and encodes it to the output.
        '''
        self.writer.writerow([s.encode("utf-8") for s in row])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class UnicodeDictWriter:
    def __init__(self, f, fieldnames, restval="", extrasaction="raise",
                 dialect="excel", *args, **kwds):
        self.fieldnames = fieldnames    # list of keys for the dict
        self.restval = restval          # for writing short dicts
        if extrasaction.lower() not in ("raise", "ignore"):
            raise ValueError, \
                  ("extrasaction (%s) must be 'raise' or 'ignore'" %
                   extrasaction)
        self.extrasaction = extrasaction
        self.writer = UnicodeWriter(f, dialect, *args, **kwds)

    def writeheader(self):
        header = dict(zip(self.fieldnames, self.fieldnames))
        self.writerow(header)

    def _dict_to_list(self, rowdict):
        if self.extrasaction == "raise":
            wrong_fields = [k for k in rowdict if k not in self.fieldnames]
            if wrong_fields:
                raise ValueError("dict contains fields not in fieldnames: "
                                 + ", ".join([repr(x) for x in wrong_fields]))
        return [rowdict.get(key, self.restval) for key in self.fieldnames]

    def writerow(self, rowdict):
        return self.writer.writerow(self._dict_to_list(rowdict))

    def writerows(self, rowdicts):
        rows = []
        for rowdict in rowdicts:
            rows.append(self._dict_to_list(rowdict))
        return self.writer.writerows(rows)
