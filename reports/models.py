from django.db import models
from django.template.defaultfilters import date

from program_manager.models import Program


class ReportManager(models.Manager):
    def get_current(self):
        return self.latest('date_created')


class Report(models.Model):
    program = models.ForeignKey(Program, related_name='reports')
    is_current = models.NullBooleanField(blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(blank=True, null=True)
    date_completed_estimate = models.DateTimeField(blank=True, null=True)

    records = models.PositiveIntegerField(default=0)
    duplicate_groups = models.PositiveIntegerField(default=0)
    duplicate_records = models.PositiveIntegerField(default=0)
    normalized_records = models.PositiveIntegerField(default=0)
    junk_records = models.PositiveIntegerField(default=0)

    objects = ReportManager()

    class Meta:
        unique_together = ('program', 'is_current')
        ordering = ['-date_created']

    @property
    def date_created_formatted(self):
        return date(self.date_created, 'SHORT_DATETIME_FORMAT')

    @property
    def date_completed_or_estimate_formatted(self):
        dt = self.date_completed or self.date_completed_estimate

        if self.date_completed:
            return date(dt, 'SHORT_DATETIME_FORMAT')

        if self.date_completed_estimate:
            return '{} (Est.)'.format(date(dt, 'SHORT_DATETIME_FORMAT'))


class QualityScoreReport(models.Model):
    program = models.OneToOneField(Program)

    def get_current_quality_score(self):
        """Returns the most recently calculated Quality Score object"""
        return self.program.quality_scores.latest('created')

    def get_all_quality_scores(self):
        return self.program.quality_scores.order_by('created')


class LogsReport(models.Model):
    """ Detailed logging output related to a program """

    program = models.OneToOneField(Program)
