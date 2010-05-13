from django.db import models
from django.contrib.auth.models import User
from main.models import Tag, Song, Band

class ProjectVersion(models.Model):
    project = models.ForeignKey('Project')
    title = models.CharField(max_length=100)
    song = models.ForeignKey(Song)
    version = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User)

class Project(models.Model):
    band = models.ForeignKey(Band)
    date_activity = models.DateTimeField(auto_now=True)

    # False if this project supports concurrent editing
    can_check_out = models.BooleanField()

    # who has it checked out, null if nobody
    checked_out_to = models.ForeignKey(User, null=True, blank=True, related_name='checked_out_to')

    # False if scrapped
    visible = models.BooleanField(default=True)

    # if this project is a fork, what projectversion is it forked from?
    forked_from = models.ForeignKey('ProjectVersion', null=True, blank=True, related_name='forked_from')
    merged_from = models.ManyToManyField('ProjectVersion', null=True, blank=True, related_name='merged_from')

    tags = models.ManyToManyField(Tag, blank=True)

    scrap_voters = models.ManyToManyField(User, blank=True, related_name='scrap_voters')
    promote_voters = models.ManyToManyField(User, blank=True, related_name='promote_voters')
    subscribers = models.ManyToManyField(User, related_name='project_subscribers')

    def __unicode__(self):
        return self.title


    def get_latest_version(self):
        versions = ProjectVersion.objects.filter(project=self).order_by('-version')
        if versions.count() > 0:
            return versions[0]
        else:
            return None
