from __future__ import absolute_import

from django.db.models import Q

from celery import shared_task
from rl_proto2.celery import app, JobTask
from celery.utils.log import get_task_logger
from program_manager.models import Program
from program_manager.forms import DefaultSurvivingRecordRuleForm

import re
import signal
import datetime


logger = get_task_logger(__name__)


@shared_task(bind=True, base=JobTask)
def run_program(self, program_pk):
    program = Program.objects.get(pk=program_pk)
    # handle revoke
    def term_handler(signum, frame):
        print 'Caught SIGABRT signal, pausing program.'
        program.data_source.pause()
    signal.signal(signal.SIGABRT, term_handler) # TODO: restore default
    logger.info('Executing program #{0}'.format(program_pk))
    program.run()
    logger.info('Program #{0} executed.'.format(program_pk))


@shared_task
def run_scheduled_program(self, program_pk):
    program = Program.objects.get(pk=program_pk)
    print 'running scheduled %s' % program.pk


@shared_task(base=JobTask)
def download_schema(program_pk):
    program = Program.objects.get(pk=program_pk)
    program.source.update_schema()

    lead_table = program.source.get_table('Lead')

    # default rules
    main_email_field = lead_table.get_main_email_field()
    if main_email_field:
        program.dupmatchrule_set.create(priority=0, field=main_email_field)
    field = lead_table.fields.get(salesforcefield__name='LastModifiedDate')
    program.survivingrecordrule_set.create(priority=DefaultSurvivingRecordRuleForm.priority, field=field, rule='NEWEST')
    field = lead_table.fields.get(salesforcefield__name='LeadSource')
    program.survivingvaluerule_set.create(priority=0, field=field, rule='OLDEST')


@shared_task
def estimate_program_time(program_pk):
    estimate_time_per_record_in_secs = 0.53451

    inspect = app.control.inspect()
    active = inspect.active()

    # count records queued
    total_records = 0
    programs_running = []
    for tasks in active.values():
        for task in tasks:
            if task['name'] == 'program_manager.tasks.run_program':
                pk = re.findall('\d+', task['args'])[0]
                programs_running.append(pk)

    queued_programs = list(Program.objects.filter(
        Q(pk__in=programs_running) | Q(pk=program_pk)))

    for qprog in queued_programs:
        total_records += qprog.count_records

    estimate = datetime.timedelta(
        seconds=total_records * estimate_time_per_record_in_secs)

    program = Program.objects.get(pk=program_pk)

    report = program.latest_report
    report.date_completed_estimate = report.date_created + estimate
    report.save()

    program.emit('program_changed', note='estimation')
