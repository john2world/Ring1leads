web: gunicorn rl_proto2.wsgi --log-file -
worker: celery -A rl_proto2 worker -l info -B -S djcelery.schedulers.DatabaseScheduler --concurrency 8
