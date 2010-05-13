from django.db import models
from django.contrib.auth.models import User
from main.models import *

class BandInvitation(models.Model):
    """
    An invitation from a user to join their band. It can be a code, which is
    redeemed by hyperlink, or a direct invitation.
    """
    # who sent the invite
    inviter = models.ForeignKey(User, related_name="inviter")
    band = models.ForeignKey(Band)
    timestamp = models.DateTimeField(auto_now_add=True)
    role = models.IntegerField(choices=ROLE_CHOICES, default=BAND_MEMBER)

    # when the invite becomes inactive. null means never
    # (only applies if isLink() is True)
    expire_date = models.DateTimeField(null=True, blank=True)

    # how many people can join the band based on this a
    # (only applies if isLink() is True)
    count = models.IntegerField(default=1)

    # password to join the band if this is a hyperlink
    code = models.CharField(max_length=256, null=True, blank=True)
    # user if this is a direct invitation
    invitee = models.ForeignKey(User, null=True, blank=True, related_name="invitee")

    def isLink(self):
        return not (self.code is None)

    def redeemHyperlink(self):
        if self.code is None:
            return None
        else:
            from django.core.urlresolvers import reverse
            return reverse('redeem_invitation', args=[self.code])

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
