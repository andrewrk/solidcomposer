from django_extensions.management.jobs import BaseJob

from datetime import datetime, timedelta
from main.models import *

import os

class Job(BaseJob):
    "deletes old temp files"
    help = __doc__

    def execute(self):
        now = datetime.now()
        tempfiles = TempFile.objects.filter(death_time__lte=now)

        for tempfile in tempfiles:
            try:
                os.remove(tempfile.path)
            except OSError:
                pass

            tempfile.delete()
        
