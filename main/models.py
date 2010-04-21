from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    artist_name = models.CharField(max_length=256)
    activated = models.BooleanField()
    activate_code = models.CharField(max_length=256)
    date_activity = models.DateTimeField(auto_now=True)
    logon_count = models.IntegerField()

    def __unicode__(self):
        return self.user.username
