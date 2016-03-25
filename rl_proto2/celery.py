from __future__ import absolute_import
import os
import rollbar
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rl_proto2.settings')

# initialize rollbar
rollbar.init(settings.ROLLBAR['access_token'],
              environment=settings.ROLLBAR['environment'])



app = Celery('rl_proto2')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERY_RESULT_SERIALIZER='msgpack',
    CELERY_MESSAGE_COMPRESSION='gzip',
    CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
)

if not 'on_heroku' in os.environ:
    app.conf.update(CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend')
else:
    app.conf.update(CELERY_S3_BACKEND_SETTINGS = {
        'aws_access_key_id': 'AKIAI2EWHSN6LCJEV2WA',
        'aws_secret_access_key': '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',
        'bucket': 'ringlead-dqp-001',
    })

    app.conf.update(CELERY_RESULT_BACKEND='celery_s3.backends.S3Backend')


class JobTask(app.Task):
    '''
    Automatically manage a task associated with a Program.
    '''
    abstract = True

    def __init__(self, *args, **kwargs):
        super(JobTask, self).__init__(*args, **kwargs)

    @property
    def job(self):
        from program_manager.models import Job
        return Job.get(self.request.id)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        from program_manager.models import Job
        job = Job.get(task_id)
        job.status = status
        if status == 'SUCCESS':
            job.progress = 100
        job.save()

