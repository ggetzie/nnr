from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

# upload media from users to a separate bucket
# so it can be processed before being served from the public bucket
class RawMediaStorage(S3Boto3Storage):
    bucket_name = settings.RAW_MEDIA_BUCKET
