import datetime
import uuid

from annoying.fields import AutoOneToOneField

from django.db import models
from django.utils.functional import cached_property

from celery.result import AsyncResult
from polymorphic import PolymorphicModel

import jsonfield

from accounts.models import CustomUser as CustomUser
from events.models import EventSourceMixin
from integrations.models import ExternalTable, ExternalField, Source, FileSource
from program_manager.choices import *
from program_manager import managers
from program_manager.signals import program_end, program_start, program_begin
from project_utils.models import SerializableModelMixin, ModelDiffMixin


class Program(ModelDiffMixin, EventSourceMixin, SerializableModelMixin, PolymorphicModel):
    """A generic job that contains a connected system (e.g. Salesforce), some
    defined actions and some granular settings."""

    user = models.ForeignKey(CustomUser)
    source = models.ForeignKey(Source, null=True, related_name='programs')
    created = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=False)
    status = models.CharField(max_length=256, choices=STATUSES, default='CREA')
    data_origin = models.CharField(max_length=32, default='SALESFORCE', null=True, blank=True, choices=PROGRAM_SOURCES)
    table_schema = models.ForeignKey(ExternalTable, null=True)
    dedupe = models.BooleanField(default=True)
    analyze_only = models.BooleanField(default=False)
    location_optimization = models.BooleanField(default=False)
    contacts_normalization = models.BooleanField(default=True)
    junk_removal = models.BooleanField(default=True)
    tags = models.CharField(max_length=2048, null=True, blank=True)
    pre_backup_url = models.URLField(max_length=256, null=True, blank=True)
    post_run_url = models.URLField(max_length=256, null=True, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    current_activity_description = models.CharField(max_length=256, null=True, blank=False)
    schedule_enabled = models.BooleanField(default=False)
    schedule_day = models.CharField(max_length=64, null=True, blank=False, default=DAYS_OF_WEEK[0][0], choices=DAYS_OF_WEEK)
    schedule_hour = models.TimeField(null=True, blank=False)
    resume_data = jsonfield.JSONField(null=True, blank=True)
    # # Person Info Optimization Options
    # person_name_proper_case = models.BooleanField(default=True)
    # # Company Info Optimization Options
    # address_optimize = models.BooleanField(default=True)
    # phone_optimize = models.BooleanField(default=True)

    objects = managers.ProgramManager()

    class Meta:
        ordering = ['-created']

    def __init__(self, *args, **kwargs):
        super(Program, self).__init__(*args, **kwargs)
        self.data_source = None

    def __unicode__(self):
        return self.name or 'unnamed'

    def save(self, *args, **kwargs):
        if not self.name:
            self.set_temp_name()

        has_changed = self.has_changed
        super(Program, self).save(*args, **kwargs)

        if has_changed:
            self.emit('program_changed')

    def begin(self, analyse_only=False):
        from qscore.models import QualityScore
        from program_manager import tasks as program_manager_tasks
        self.analyze_only = analyse_only

        # reset data urls
        self.pre_backup_url = ''
        self.post_run_url = ''

        self.status = 'RUN'
        self.save()

        QualityScore.objects.create(program=self)
        self.start_job(program_manager_tasks.run_program, self.pk)

        program_begin.send(None, program=self)

    def run(self):
        if isinstance(self.source, FileSource):
            self.analyze_only = True

        self.status = 'RUN'

        self.last_run = datetime.datetime.now()
        self.save()

        program_start.send(None, program=self)

        self.data_source = self.source.setup_data_source(self)
        self.data_source.launch()

        post_run_writer = self.data_source.get_writer('PostRunWriter')

        self.refresh_from_db()
        self.pre_backup_url = self.data_source.s3_backup_url
        self.post_run_url = post_run_writer.post_run_url
        self.status = 'COMPL'
        self.save()

        program_end.send(None, program=self, result=post_run_writer.result)

    @cached_property
    def count_records(self):
        return self.source.count_records(self)

    @cached_property
    def latest_report(self):
        return self.reports.order_by('date_created').last()

    @property
    def get_cname(self):
        """Returns the class name of the current Program"""
        pdict = {
            'ListImportProgram': 'List Import',
            'BatchProgram': 'Database Program',
        }
        return str(pdict[self.__class__.__name__])

    @property
    def get_program_icon(self):
        """Returns the appropriate icon for the current program"""
        icon_dict = {
            'ListImportProgram': 'fa-file-excel-o',
            'BatchProgram': 'fa-database',
        }
        return str(icon_dict[self.__class__.__name__])

    def start_job(self, task, *args, **kwargs):
        return Job.start(self, task, *args, **kwargs)

    def cancel_current_job(self):
        self.job_set.latest('id').cancel()

    def pause(self):
        self.job_set.latest('id').pause()
        self.status = 'PAUSE'
        self.save()

    def get_current_quality_score(self):
        """Returns the most recently calculated Quality Score"""
        qs = self.get_all_quality_scores()
        return qs[0] if qs else None

    def get_all_quality_scores(self):
        """Returns the most recently calculated Quality Score"""
        return self.quality_scores.all().order_by('-id')

    def get_table_filters(self):
        """Returns all TableFilter objects related to Program"""
        return self.tablefilter_set.all()

    def get_field_filters(self):
        """Returns all FieldFilter objects related to Program"""
        return self.fieldfilter_set.all()

    def get_dup_match_rules(self):
        """Returns all DupMatchRule objects related to Program"""
        return self.dupmatchrule_set.all()

    def get_surviving_record_rules(self):
        """Returns all SurvivingRecordRule objects related to Program"""
        return self.survivingrecordrule_set.all()

    def get_surviving_value_rules(self):
        """Returns all SurvivingValueRule objects related to Program"""
        return self.survivingvaluerule_set.all()

    @property
    def is_running(self):
        return self.status == 'RUN'

    def set_temp_name(self, save=False):
        self.name = 'Program %s' % str(uuid.uuid4())[:8]

        if save:
            self.save()


class Job(models.Model):
    """ Represents a job that is downloading, transforming or updating data as
    part of a Program."""

    program = models.ForeignKey(Program)
    name = models.CharField(max_length=256)
    progress = models.PositiveSmallIntegerField(default=0) # as a percentage
    task_id = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=128, choices=JOB_STATUSES, default='PENDING')
    paused = models.BooleanField(default=False)

    @staticmethod
    def start(program, task, *args, **kwargs):
        result = task.delay(*args, **kwargs)
        name = '%s.%s' % (task.__module__, task.__name__)
        job = program.job_set.create(task_id=result.id, name=name)
        job.celery_task = result
        return job

    @staticmethod
    def get(task_id):
        return Job.objects.get(task_id=task_id)

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.celery_task = None

    def __unicode__(self):
        return '%s (%s)' % (self.id, self.name)

    def get_celery_task(self):
        if not self.celery_task:
            self.celery_task = AsyncResult(self.task_id)
        return self.celery_task

    def update_from_task(self):
        self.status = self.get_celery_task().state
        self.save()

    def pause(self):
        self.get_celery_task().revoke(terminate=True, signal='SIGABRT')

    def cancel(self):
        self.get_celery_task().revoke(terminate=True)

    def resume(self):
        self.paused = False
        self.save()

    def update_progress(self, progress):
        self.progress = progress
        self.save()

    def is_finished(self):
        return self.get_celery_task().finished()


class TableFilter(models.Model):
    """
    A table in a connected system.  Tables can be dynamically loaded but
    in initial versions we will hard-code available tables and present these
    table options based on the connected system.
    """

    program = models.ForeignKey(Program, null=True, blank=True)
    table_name = models.CharField(max_length=256)  # ex. 'LEAD'


class FieldFilter(models.Model):
    """
    A field in a connected system and corresponding values that allow the
    user to determine a subset of their records.

    program: the related program
    field: field to filter on from a database table schema
    operator: the appropriate operator based on field type (e.g. >, <, =, older than)
    field_value: a single value or comma-separated values that would make the
    filter true
   """

    program = models.ForeignKey(Program, null=True, blank=False)
    field = models.ForeignKey(ExternalField)
    operator = models.CharField(max_length=256, default='=', choices=TEXT_OPERATORS+NUM_OPERATORS+DATETIME_OPERATORS+BOOL_OPERATORS)
    field_value = models.CharField(max_length=256, null=True, blank=True)


# class DateFieldFilter(FieldFilter):
#     operator = models.CharField(max_length=256, choices=DATETIME_OPERATORS)
#     value = models.DateField()


class DupMatchRule(models.Model):
    priority = models.IntegerField()
    program = models.ForeignKey(Program, null=True, blank=True)
    field = models.ForeignKey(ExternalField)
    rule = models.CharField(
        max_length=256,
        choices=MATCH_OPERATORS,
        default='EXACT'
        )

    class Meta:
        ordering = ['priority']


class SurvivingRecordRule(models.Model):
    priority = models.IntegerField()
    program = models.ForeignKey(Program, null=True, blank=False)
    field = models.ForeignKey(ExternalField)
    rule = models.CharField(
        max_length=256,
        choices=SR_AGE_OPTIONS+SR_NUMBER_OPTIONS+TEXT_OPERATORS+BOOL_OPERATORS,
        default='NEWEST'
        )
    value = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ['priority']


class SurvivingValueRule(models.Model):
    priority = models.IntegerField()
    program = models.ForeignKey(Program, null=True, blank=False)
    field = models.ForeignKey(ExternalField)
    # field_type = models.CharField(max_length=256)
    rule = models.CharField(
        max_length=256,
        choices=SV_AGE_OPERATORS+SV_NUMBER_OPERATORS+SV_TEXT_OPERATORS+TEXT_OPERATORS+PICKLIST_OPERATORS+BOOL_OPERATORS,
        default='ADD'
        )
    value = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ['priority']


class LocationOptimizationRule(models.Model):
    priority = models.IntegerField()
    program = models.ForeignKey(Program, null=True, blank=True, related_name='location_optimization_rules')
    field = models.ForeignKey(ExternalField)
    rule = models.CharField(
        max_length=256,
        choices=UPDATE_POLICY_CHOICES,
        default='OVERWRITE'
        )

    class Meta:
        ordering = ['priority']


class ContactsNormalizerRule(models.Model):
    priority = models.IntegerField()
    program = models.ForeignKey(Program, null=True, blank=True, related_name='contacts_normalizer_rules')
    field = models.ForeignKey(ExternalField)
    broadlook_field_name = models.CharField(max_length=256)  # i.e. JobTitle
    broadlook_rule_name = models.CharField(max_length=256)  # i.e. Case
    rule = models.CharField(max_length=256)

    class Meta:
        ordering = ['priority']

    @property
    def api_field_name(self):
        return '{0}.{1}'.format(self.broadlook_field_name, self.broadlook_rule_name)


class JunkRemovalSettings(models.Model):
    program = AutoOneToOneField(Program, null=True, blank=True, related_name='junk_removal_settings')
    delete_spam_records = models.BooleanField(default=True)
