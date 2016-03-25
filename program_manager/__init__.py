from django.apps import AppConfig
from django.template.loader import render_to_string
from django.utils import timezone

from program_manager.tasks import estimate_program_time
from program_manager.signals import program_start, program_end, program_begin, update_progress
from notifications.models import Notification
from reports.models import Report


default_app_config = 'program_manager.ProgramManagerConfig'


class ProgramManagerConfig(AppConfig):
    name = 'program_manager'
    verbose_name = 'Program Manager'

    def ready(self):
        program_begin.connect(self.estimate_program_time)
        program_start.connect(self.emit_program_start)

        program_end.connect(self.on_program_end)
        program_end.connect(self.update_program_report)
        program_end.connect(self.notify_program_finished)

        update_progress.connect(self.update_progress)

    def on_program_end(self, program, result, **kwargs):
        program.current_activity_description = None
        program.save()

    def update_program_report(self, program, result, **kwargs):
        Report.objects.filter(
            program=program, is_current=True
        ).update(
            is_current=None, date_completed=timezone.now(), **result
        )

        program.emit('program_changed', note='finished')

    @staticmethod
    def estimate_program_time(program, **kwargs):
        Report.objects.filter(
            program=program, is_current=True
        ).update(
            is_current=None
        )

        Report.objects.create(program=program, is_current=True)

        program.emit('program_changed', note='begin')

        estimate_program_time.delay(program.pk)

    @staticmethod
    def update_progress(program, progress, current_activity_description, **kwargs):
        program.progress = progress
        program.current_activity_description = current_activity_description
        program.save()

    @staticmethod
    def notify_program_finished(program, result, **kwargs):
        user = program.user
        template_name = 'program_manager/notifications/program_end.html'
        subject = 'Your program, {}, is complete'.format(program.name)

        Notification.objects.create(
            sharedwith=str(user.pk),
            subject=subject,
            text=render_to_string(template_name, context={
                'program': program,
                'program_ended': timezone.now(),
                'program_result': result,
            }))

    @staticmethod
    def emit_program_start(program, **kwargs):
        program.emit('program_changed', note='started')
