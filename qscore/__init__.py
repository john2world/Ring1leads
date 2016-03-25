from django.apps import AppConfig
from django.db.models import signals as db_signals

from operations import phone_validators


default_app_config = 'qscore.QualityScoreConfig'


__all__ = (
    'phone_validators',
    'default_app_config',
    'QualityScoreConfig',
)


class QualityScoreConfig(AppConfig):
    name = 'qscore'
    verbose_name = 'qscore'

    def ready(self):
        from qscore.models import QualityScore

        db_signals.post_save.connect(
            self.create_qualityscorereport, sender=QualityScore)

    def create_qualityscorereport(self, instance, **kwargs):
        """ Once QualityScore is created, we create a QualityScoreReport
            object for that program.
        """
        from reports.models import QualityScoreReport

        program = instance.program

        if not hasattr(program, 'qualityscorereport'):
            QualityScoreReport.objects.create(program=program)
