from sys import exit
from itertools import chain

from rl_proto2.celery import app


def run():
    active = app.control.inspect().active()
    running_jobs = list(chain(*active.values()))

    if running_jobs:
        for job in running_jobs:
            print('Running: {}'.format(job['name']))
        exit(len(running_jobs))

    print('No jobs running')
