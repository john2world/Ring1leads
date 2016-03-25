from django.db import models
from program_manager.models import Program


class QualityScore(models.Model):
    """ Represents a score at a single point in time."""

    program = models.ForeignKey(Program, related_name='quality_scores')
    created = models.DateTimeField(auto_now_add=True)
    score = models.PositiveSmallIntegerField(null=True)
    percent_valid_location = models.PositiveSmallIntegerField(null=True, blank=True)
    percent_valid_phone = models.PositiveSmallIntegerField(null=True, blank=True)
    percent_valid_email = models.PositiveSmallIntegerField(null=True, blank=True)
    percent_spam_email = models.PositiveSmallIntegerField(null=True, blank=True)
    percent_complete = models.PositiveSmallIntegerField(null=True, blank=True)
    avg_age = models.PositiveSmallIntegerField(null=True, blank=True)  # Number of days
    avg_since_last_modified = models.PositiveSmallIntegerField(null=True, blank=True)  # Num days

    def __unicode__(self):
        return str(self.score) + " | " + self.program.name
