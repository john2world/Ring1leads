import csv
from itertools import izip
import os
import struct
import msgpack
import kyotocabinet as kc
import numpy as np
from operations.dedupe import Deduper
from tempfile import NamedTemporaryFile
from salesforce_bulk import CsvDictsAdapter
from integrations.storage import open_s3, s3_public_url
from integrations.salesforce.soap import SalesforceSOAP
from integrations.salesforce.utils import CustomSalesforceBulk
from program_manager.signals import update_progress

class PauseException(Exception):
    pass

class GenericDataSource(object):
    """
    Interface for a source of streamed data from a client database.
    """
    def __init__(self, identifier, *args, **kwargs):
        self.kwargs = kwargs
        self.identifier = identifier
        self.local_storage = NamedTemporaryFile(prefix='rl_', delete=True)
        self.s3_backup = open_s3(self.identifier, 'wb')
        self.database_file = NamedTemporaryFile(prefix='rldb_', delete=True)
        self.database = kc.DB()
        print 'Local database saved to %s' % self.database_file.name
        self.database.open(self.database_file.name + '#type=kch', kc.DB.OWRITER | kc.DB.OCREATE)
        self.processors = []
        self.writers = []
        self.record_count = 0
        self.pause_requested = False
        self.resume_data = {}

    def save_for_resume(self, key, value):
        self.resume_data[key] = value

    def persist_resume_data(self):
        raise NotImplementedError

    def launch(self):
        try:
            self.fetch(**self.kwargs)
            self.finish_fetch()
        except PauseException:
            # paused while fetching data, just throw everything away
            # TODO: we could probably continue the fetch, at least in the Salesforce case.
            print 'Paused while fetching data, discarding everything...'
            return False
        # TODO: save data for next run
        print 'DataSource ready, beggining first pass...'
        self.first_pass()
        self.write_pass()
        try:
            self.local_storage.close()
            self.database.close()
            self.database_file.close()
        except PauseException:
            print 'Paused while exiting, finishing anyway...'
            # we're done anyway
            self.local_storage.close()
            self.database.close()
            self.database_file.close()
            return True
        return True

    def pause(self):
        self.pause_requested = True
        raise PauseException

    def register_processor(self, processor_class, *args, **kwargs):
        kwargs['source'] = self
        processor = processor_class(*args, **kwargs)
        self.processors.append(processor)
        return processor

    def get_processor(self, processor_name):
        return next((p for p in self.processors if p.__class__.__name__ == processor_name), None)

    def register_writer(self, writer_class, *args, **kwargs):
        kwargs['source'] = self
        writer = writer_class(*args, **kwargs)
        self.writers.append(writer)
        return writer

    def get_writer(self, writer_name):
        return next((w for w in self.writers if w.__class__.__name__ == writer_name), None)

    def fetch(self, **kwargs):
        raise NotImplementedError('Fetch method not implemented in data source.')

    def finish_fetch(self):
        self.local_storage.flush()
        self.local_storage.seek(0)
        self.s3_backup.close()
        self.s3_backup_url = s3_public_url(self.s3_backup)

    def process_chunk(self, chunk):
        """
        Receive a chunk of data directly (CSV or others).
        """
        if isinstance(chunk, basestring):
            self.s3_backup.write(chunk)
        else:
            self.s3_backup.write(chunk.tobytes()) # memoryview not allowed
        #self.s3_backup.write('empty... for now')
        self.local_storage.write(chunk)

    def save(self, row, key=None):
        key = key or struct.pack('<I', row['_id'])
        self.database.set(key, msgpack.packb(row))

    def load(self, id):
        return msgpack.unpackb(self.database.get(struct.pack('<I', id)))

    def merge(self, canonical, cluster):
        raise NotImplementedError('merge method not implemented in data source.')

    def first_pass(self):
        try:
            for row in csv.DictReader(open(self.local_storage.name, 'rbU')):
                row['_id'] = self.record_count
                self.record_count += 1
                self.save(row)
        except PauseException:
            print 'Paused while loading data into db.'
            pass

        for processor in self.processors:
            for i in xrange(0, self.record_count):
                row = self.load(i)
                row = processor.receive_row(row) or row
                self.save(row)
            processor.finish()

        print 'DataSource processed %s records.' % self.record_count
        self.local_storage.seek(0)

    def write_pass(self):
        print 'Starting DataSource write process.'
        # TODO: profile and change this to a cursor index with a tree kc
        for i in range(0, self.record_count):
            row = self.load(i)
            for writer in self.writers:
                writer.write_row(row)
        for writer in self.writers:
            writer.finish()
        print 'Finished DataSource write process.'


class ProgramDataSource(GenericDataSource):
    """
    Base class for a data source used by Batch and List Import programs.
    Accepts program as positional argument.
    Provides hooks for program's quality score calculations.
    """
    def __init__(self, identifier, program, *args, **kwargs):
        super(ProgramDataSource, self).__init__(identifier, *args, **kwargs)
        self.program = program
        self.qs_instance = self.program.get_current_quality_score()
        self.quality_score = 0.0
        self.qs_processors_count = 0
        self.succeeded_qs_processors_count = 0
        self.qs_results = []
        self.current_step = 0

    def persist_resume_data(self):
        self.program.refresh_from_db()
        self.program.resume_data = self.resume_data
        self.program.save()

    def fetch(self, **kwargs):
        self.set_progress('Fetch', 'Preparing data.')

    def set_progress(self, process_str, description):
        percent_complete = self.current_step * 100 / (len(self.processors) + len(self.writers))
        update_progress.send(None, program=self.program, progress=percent_complete,
                             current_activity_description=description)
        print 'Program #{0}: {3}% complete | Current step: {1} ({2}) '.format(self.program.pk, self.current_step,
                                                                              process_str, percent_complete)

    def register_processor(self, processor_class, *args, **kwargs):
        processor = super(ProgramDataSource, self).register_processor(processor_class, *args, **kwargs)

        if processor.calculates_score():
            self.qs_processors_count += 1

        return processor

    def first_pass(self):
        for row in csv.DictReader(open(self.local_storage.name, 'rbU')):
            row['_id'] = self.record_count
            self.record_count += 1
            self.save(row)

        qscore_step_num = 1
        for processor in self.processors:
            self.current_step += 1
            self.set_progress(processor.__class__.__name__, processor.ACTIVITY_DESCRIPTION)
            for i in xrange(0, self.record_count):
                row = self.load(i)
                row = processor.receive_row(row) or row
                self.save(row)
            processor.finish()

            if processor.calculates_score():
                qs_result, quality_score_points = processor.calculate_score(qscore_step_num)
                self.quality_score += quality_score_points
                self.qs_results.append(qs_result)

                if qscore_step_num == self.qs_processors_count:
                    for result_dict in self.qs_results:
                        qs_field_name = result_dict.get('name')
                        qs_result_value = result_dict.get('value')

                        if not qs_field_name or qs_result_value is None:
                            continue

                        self.succeeded_qs_processors_count += 1

                        setattr(self.qs_instance, qs_field_name, qs_result_value)

                    if self.succeeded_qs_processors_count:
                        self.qs_instance.score = (self.quality_score * 100) / (self.succeeded_qs_processors_count * 10)
                        self.qs_instance.save()
                else:
                    qscore_step_num += 1

        print 'DataSource processed %s records.' % self.record_count
        print 'CALCULATED QUALITY SCORE: {0}'.format(self.qs_instance.score)
        self.local_storage.seek(0)

    def write_pass(self):
        print 'Starting DataSource write process.'
        # TODO: profile and change this to a cursor index with a tree kc
        for i in range(0, self.record_count):
            row = self.load(i)
            for writer in self.writers:
                writer.write_row(row)
        for writer in self.writers:
            self.current_step += 1
            self.set_progress(writer.__class__.__name__, writer.ACTIVITY_DESCRIPTION)
            writer.finish()
        print 'Finished DataSource write process.'

    def remove_metadata(self, row):
        flags = ['_id', '_write', '_delete', '_merge_into', '_merge_with', '_normalized']
        for flag in flags:
            if flag in row:
                del row[flag]


class QualityScoreMixin(object):
    DEFAULT_SAMPLE_SIZE = 100
    SCORE_RANGES = {}

    def get_random_ids(self):
        if not self.source.record_count:
            return []

        sample_size = self.DEFAULT_SAMPLE_SIZE if self.source.record_count >= self.DEFAULT_SAMPLE_SIZE \
            else self.source.record_count

        return np.random.randint(low=0, high=self.source.record_count, size=sample_size)

    def calculate_score(self, step_num):
        if not self.SCORE_RANGES:
            return {}, 0.0

        ranges = self.SCORE_RANGES['ranges']
        left = self.SCORE_RANGES['left']
        right = self.SCORE_RANGES['right']

        qscore_value = self.get_qscore_value()

        if qscore_value is None:
            return {}, 0

        result_dict = {
            'name': self.SCORE_RANGES.get('name', None),
            'value': qscore_value
        }

        for side_score in [left, right]:
            if side_score.operator(qscore_value, side_score.limit):
                return result_dict, side_score.point

        return result_dict, next((x.point for x in ranges if x.lower <= qscore_value <= x.upper), 0)

    def get_qscore_value(self):
        return None

    def calculates_score(self):
        return bool(self.SCORE_RANGES)


class DataProcessor(QualityScoreMixin):
    """
    An object that receives streamed data from a DataSource, and processes it.
    The function`receive_row`, receives all the rows in the database, one by one.
    Returning a dict from this function, or modifying the passed dict, will make
    these changes available to the next processor.
    If the changes made to the dict should be written to the client database,
    call `self.mark_for_write` with the dict as an argument.
    If the row shold be deleted from the client database, call
    `self.mark_for_deletion` on it.
    If you need to further process records in the `finish` function, you can load
    them from the local database with `self.load(_id)`.
    Metadata that shouldn't be persisted to the client database should start
    its key with an underscore.
    """

    ACTIVITY_DESCRIPTION = 'Processing records.'

    def __init__(self, *args, **kwargs):
        try:
            self.source = kwargs.pop('source')
        except KeyError:
            raise Exception('DataProcessor descendants must be registered with register_processor method')

        self.setup(**kwargs)

    def save(self, row, key=None):
        '''
        Optional key. Default is to use the '_id' key.
        '''
        self.source.save(row, key)

    def load(self, id):
        return self.source.load(id)

    def mark_for_write(self, row):
        row['_write'] = True

    def mark_for_deletion(self, row):
        row['_delete'] = True

    def emit_merge(self, canonical, cluster):
        self.source.merge(canonical, cluster)

    def setup(self, **kwargs):
        pass

    def receive_row(self, row):
        return row

    def finish(self):
        pass


class BatchDataProcessor(DataProcessor):
    def __init__(self, *args, **kwargs):
        super(BatchDataProcessor, self).__init__(*args, **kwargs)
        self.batch_size_limit = kwargs.get('batch_size_limit', 10000)
        self.current_batch = []
        self.current_batch_len = 0
        self.processed_batches_count = 0

    def finish(self):
        if self.current_batch_len:
            self.process_batch()

    def receive_row(self, row):
        if self.current_batch_len >= self.batch_size_limit:
            self.process_batch()
            self.current_batch = []
            self.current_batch_len = 0

        self.current_batch.append(row)
        self.current_batch_len += 1

    def process_batch(self):
        raise NotImplementedError('BatchDataProcessor descendants must implement process_batch method')


class DataWriter(object):

    ACTIVITY_DESCRIPTION = 'Processing write operations.'

    def __init__(self, *args, **kwargs):
        try:
            self.source = kwargs.pop('source')
        except KeyError:
            raise Exception('DataWriter descendants must be registered with register_writer method')

        self.setup(**kwargs)

    def setup(self, **kwargs):
        pass

    def write_row(self, row):
        """
        Write the row to an output database.
        """
        pass

    def load(self, id):
        return self.source.load(id)

    def remove_metadata(self, row):
        self.source.remove_metadata(row)

    def filter_keys(self, row, whitelist):
        """
        Delete all keys from a dict that aren't in the whitelist.
        """
        for key, value in row.items():
            if not key in whitelist:
                del row[key]

    def check_flag(self, row, flag):
        return flag in row and row[flag]

    def finish(self):
        pass


class SalesforceDataSource(ProgramDataSource):
    """
    Salesforce data source.
    """
    def get_bulk(self, token):
        token.refresh()
        return CustomSalesforceBulk(sessionId=token.access_token,
                                    host=token.instance_url,
                                    is_sandbox=token.is_sandbox)

    def fetch(self, token, query, updateable, **kwargs):
        super(SalesforceDataSource, self).fetch(**kwargs)
        self.updateable = updateable
        bulk = self.get_bulk(token)
        connection = bulk.get_connection()
        for chunk in bulk.download_database(connection, query):
            self.process_chunk(chunk)

    def count_records(self):
        bulk = self.get_bulk(self.kwargs.get('token'))
        connection = bulk.get_connection()
        return bulk.count_records(connection, self.kwargs.get('query'))

    def first_pass(self):
        super(SalesforceDataSource, self).first_pass()


class CsvDataSource(ProgramDataSource):
    def fetch(self, **kwargs):
        super(CsvDataSource, self).fetch(**kwargs)

        if not self.program.source.file:
            raise AttributeError('Program has no associated CSV file')

        if os.path.exists(self.program.source.file.url):
            self.local_storage = open(self.program.source.file.url, 'rbU')
            self.s3_backup.write('temp')  # TODO: handle this properly
        elif 'amazonaws' in self.program.source.file.url:
            fname, ext = os.path.splitext(os.path.basename(self.program.source.file.url))

            for chunk in open_s3(fname, 'rb'):
                self.process_chunk(chunk)


class DedupeDataProcessor(DataProcessor):
    """
    Generates a list of duplicate records, and merges each group into a single
    canonical record.
    """

    ACTIVITY_DESCRIPTION = 'Calculating duplicates.'

    def setup(self, **kwargs):
        self.deduper = Deduper(self.source.program.dupmatchrule_set.all(),
                               self.source.program.survivingrecordrule_set.all(),
                               self.source.program.survivingvaluerule_set.all())

    def receive_row(self, row):
        self.deduper.feed_record(row)

    def finish(self):
        print 'Duplicate search finished, %s clusters' % len(self.deduper.clusters)
        print 'Beggining canonical record calculations.'
        count = 0
        for key, cluster in self.deduper.clusters.viewitems():
            cluster_data = map(self.load, cluster)
            cluster_data = self.deduper.sort_cluster(cluster_data)
            canonical = self.deduper.get_canonical(cluster_data)
            canonical['_merge_with'] = [r['_id'] for r in cluster_data[1:]]
            self.save(canonical)
            for record in cluster_data[1:]:
                record['_merge_into'] = cluster_data[0]['_id']
                record['_write'] = False  # we don't want to write to dead records
                self.save(record)
            count += 1
        print 'Finished calculating canonical records.'

class DebugWriter(DataWriter):

    def write_row(self, row):
        if '_write' in row:
            #print row
            pass

class SalesforceWriter(DataWriter):
    """
    Write changes to Salesforce.
    """

    ACTIVITY_DESCRIPTION = 'Writing optimized records to your Salesforce database.'

    def setup(self, token, updateable):
        self.token = token
        self.token.refresh()
        self.update_batch = []
        self.delete_batch = []
        self.updateable = updateable
        self.soap = SalesforceSOAP(token)
        self.refresh_bulk()
        self.update_job = self.bulk.create_update_job('Lead')
        self.delete_job = self.bulk.create_delete_job('Lead')

    def refresh_bulk(self):
        self.token.refresh()
        self.bulk = CustomSalesforceBulk(sessionId=self.token.access_token,
                                         host=self.token.instance_url,
                                         is_sandbox=self.token.is_sandbox)

    def write_row(self, row):
        if '_merge_into' in row:
            pass
        elif '_write' in row and row['_write']:
            row = dict(row)
            self.filter_keys(row, self.updateable + ['Id'])
            self.update_batch.append(row)
        elif '_delete' in row and row['_delete']:
            self.delete_batch.append({'Id': row['Id']})
        elif '_merge_with' in row:
            cluster = map(self.load, row['_merge_with'])
            cluster.insert(0, row)
            self.merge(cluster, canonical=row)
        if len(self.update_batch) == 10000:
            self.dispatch_update_batch()
        if len(self.delete_batch) == 10000:
            self.dispatch_delete_batch()

    def merge(self, cluster, canonical):
        self.soap.merge_group(cluster, canonical, self.updateable)

    def finish(self):
        self.dispatch_update_batch()
        self.dispatch_delete_batch()
        # print 'Update job status:'
        # FIXME: get results and make sure there aren't any errors
        # print self.bulk.job_batches_status(self.update_job)
        self.commit_merges()
        self.soap.log.close()
        print 'FINISHED MERGE: %s' % s3_public_url(self.soap.log)

    def commit_merges(self):
        print 'Starting SOAP merge operations.'

        for result_batch, merge_batch in izip(self.soap.commit_merges(), self.soap.merge_batches):
            for merge_result, merge_request in izip(result_batch, merge_batch):
                # print merge_result
                if not hasattr(merge_result, 'errors'):
                    continue

                for error in merge_result.errors:
                    # print 'ERROR: {0}'.format(error.statusCode)
                    if error.statusCode == 'FIELD_FILTER_VALIDATION_EXCEPTION':
                        self.update_batch.append(self.soap_obj_to_dict(merge_request.masterRecord))

                        if len(self.update_batch) == 10000:
                            self.update_batch = list(np.unique(self.update_batch))
                            self.dispatch_update_batch()

                        for to_delete_id in merge_request.recordToMergeIds:
                            # https://github.com/heroku/salesforce-bulk ->
                            # When deleting you should only submit the Id for each record.
                            self.delete_batch.append({'Id': to_delete_id})

                            if len(self.delete_batch) == 10000:
                                self.delete_batch = list(np.unique(self.delete_batch))
                                self.dispatch_delete_batch()

        self.soap.merge_batches = []
        self.dispatch_update_batch()
        self.dispatch_delete_batch()

    def soap_obj_to_dict(self, soap_obj):
        d = {'Id': soap_obj.Id}

        for key, value in soap_obj.__dict__.viewitems():
            if value and key in self.updateable:
                d[key] = value

        return d

    def dispatch_update_batch(self):
        # TODO: verify 1GB limit
        if self.update_batch:
            print 'Sending update batch with %s records.' % len(self.update_batch)
            self.refresh_bulk()
            self.bulk.post_bulk_batch(self.update_job, CsvDictsAdapter(iter(self.update_batch)))
            self.update_batch = []

    def dispatch_delete_batch(self):
        # TODO: verify 1GB limit
        if self.delete_batch:
            self.refresh_bulk()
            print 'Sending delete batch with %s records.' % len(self.delete_batch)
            self.bulk.post_bulk_batch(self.delete_job, CsvDictsAdapter(iter(self.delete_batch)))
            self.delete_batch = []


class PostRunWriter(DataWriter):

    ACTIVITY_DESCRIPTION = 'Generating post-run report.'

    def setup(self, name):
        self.name = name
        #self.s3_file = open('post_run_data.csv', 'wb')
        self.s3_file = open_s3(name + '_post_run_data', 'wb')
        self.writer = None
        self.cluster_id = 0
        self.result = {
            'records': 0,
            'duplicate_groups': 0,
            'duplicate_records': 0,
            'normalized_records': 0,
            'junk_records': 0,
        }

    def setup_writer(self, row):
        initial = ['Dedupe', 'Deleted', 'Dupe cluster', 'Dedupe: details', 'Normalization']
        header = initial + [key for key in row.keys() if key not in initial]
        self.writer = csv.DictWriter(self.s3_file, fieldnames=header)
        self.writer.writeheader()

    def write_row(self, row):
        #if '_merge_into' in row or '_delete' in row and row['_delete']:
        #    return
        row = dict(row)
        row['Dedupe'] = '_merge_into' in row or '_merge_with' in row
        row['Deleted'] = self.check_flag(row, '_deleted')

        self.result['records'] += 1

        if row['Deleted']:
            self.result['junk_records'] += 1

        if row['Dedupe']:
            row['Dupe cluster'] = self.cluster_id

            if '_merge_into' in row:
                master_id = self.load(row['_merge_into'])['Id']
                row['Dedupe: details'] = 'Merged into %s' % master_id
            else:
                row['Dedupe: details'] = 'Canonical'
                self.cluster_id += 1
                self.result['duplicate_groups'] += 1

            self.result['duplicate_records'] += 1

        row['Normalization'] = self.check_flag(row, '_normalized')
        if row['Normalization']:
            self.result['normalized_records'] += 1

        self.remove_metadata(row)

        if not self.writer:
            self.setup_writer(row)

        self.writer.writerow(row)

    def finish(self):
        self.s3_file.close()
        self.post_run_url = s3_public_url(self.s3_file)
        print 'Finished writing post-run backup.'
        #self.post_run_url = 'http://dummy.com/dummy.csv'

