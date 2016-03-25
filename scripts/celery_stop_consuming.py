from time import sleep
from itertools import chain

from rl_proto2.celery import app


def run():
    """
    Stop all consumers and wait until all tasks to finish.
    Based on http://stackoverflow.com/a/27983145/639465

    """
    queues = app.amqp.Queues(app.conf.CELERY_QUEUES).keys()

    # cancel consumers (prevent from receiving new tasks)
    for queue in queues:
        app.control.cancel_consumer(queue)

    # wait for current tasks to finish
    inspect = app.control.inspect()

    while True:
        active = inspect.active()
        running_jobs = list(chain(*active.values()))
        if running_jobs:
            job_names = []
            for i, job in enumerate(running_jobs):
                job_names.append(job['name'])
            print('{} jobs running: {}'.format(i+1, ', '.join(job_names)))
            sleep(30)
        else:
            print('No jobs running')
            break
