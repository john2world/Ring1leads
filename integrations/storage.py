import boto
import smart_open
from boto.s3.key import Key
from django.conf import settings

connection = boto.connect_s3(settings.AWS_ACCESS_KEY_ID,
                             settings.AWS_SECRET_ACCESS_KEY)
bucket = connection.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)

def open_s3(name, mode, content_type='text/csv', extension='.csv'):
    key = Key(bucket)
    key.key = name + extension
    key.content_type = content_type
    s3_file = smart_open.smart_open(key, mode)
    s3_file._key = key
    return s3_file

def s3_public_url(smart_file):
    smart_file._key.set_acl('public-read')
    return smart_file._key.generate_url(expires_in=0, query_auth=False)
