import os
import dj_database_url
from rl_proto2.settings import ROLLBAR

# Parse database configuration from $DATABASE_URL
DATABASES = {}
DATABASES['default'] = dj_database_url.config()

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = False
DEBUG = True
ALLOWED_HOSTS = ['*']
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

###############################################################################
# Django storage settings
###############################################################################
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']

# RabbitMQ Settings
BROKER_URL = os.environ['RABBITMQ_BIGWIG_URL']

# Set Rollbar env to production
ROLLBAR['environment'] = 'production'

CORS_ORIGIN_ALLOW_ALL = True
#CORS_ORIGIN_WHITELIST = (
#    'ringlead-dqp-001.herokuapp.com',
#    'gateway.zscaler.net'
#)


