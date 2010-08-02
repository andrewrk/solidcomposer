from datetime import datetime
from django_extensions.management.jobs import HourlyJob
from main.models import TempFile
import os

class Job(HourlyJob):
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
        
