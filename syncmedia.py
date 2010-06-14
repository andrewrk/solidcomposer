"""
this script copies local media to amazon s3
"""

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from main.common import superwalk
import storage

import os

from storage.S3Storage import S3Storage

engine = S3Storage()

# media files
for filename in superwalk(settings.MEDIA_ROOT):
    rel_path = filename.replace(settings.MEDIA_ROOT, '')[1:]
    
    print("Storing %s..." % rel_path)
    engine.store(filename, rel_path, reducedRedundancy=True)

