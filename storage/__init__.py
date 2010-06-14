from .S3Storage import S3Storage
from .LocalFileStorage import LocalFileStorage
from django.conf import settings

if settings.USE_AWS:
    engine = S3Storage()
else:
    engine = LocalFileStorage()
