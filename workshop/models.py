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

class SampleFile(models.Model):
    # md5 hash of the binary data of the sample
    # null if we don't know what the hex digest of it is.
    hex_digest = models.CharField(max_length=32, unique=True)

    # where it is on disk, relative to MEDIA_ROOT
    path = models.CharField(max_length=256)

class SampleDependency(models.Model):
    # the file title of the dependency. it may contain path 
    # separators in the form of forward slashes.
    title = models.CharField(max_length=512)

    # link to the sample file. null if the link is unresolved.
    sample_file = models.ForeignKey(SampleFile, null=True, blank=True)

class EffectDependency(models.Model):
    # the name of the effect. this identifies it.
    title = models.CharField(max_length=256, unique=True)

class GeneratorDependency(models.Model):
    # the name of the generator. this identifies it.
    title = models.CharField(max_length=256, unique=True)

class ProjectVersion(models.Model):
    project = models.ForeignKey('Project')
    # comments, title, owner, and timestamp are in the song
    song = models.ForeignKey(Song)
    # version counter like subversion
    version = models.IntegerField()

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
        return self.get_title()

    def get_latest_version(self):
        versions = ProjectVersion.objects.filter(project=self).order_by('-version')
        if versions.count() > 0:
            return versions[0]
        else:
            return None

    def get_title(self):
        return self.get_latest_version().song.title

class Studio(models.Model):
    # e.g. FL Studio
    title = models.CharField(max_length=100)

    # studio identifier, also used as the url
    identifier = models.CharField(max_length=50, unique=True)

    # capabilities - what we can do with the studio
    # whether we have dependency support
    canReadFile = models.BooleanField()
    # whether we can merge two project files
    canMerge = models.BooleanField()
    # whether we can render a project on the server
    canRender = models.BooleanField()

    # description for info page
    info = models.TextField(blank=True)

    logo_large = models.ImageField(upload_to='img/studio', blank=True, null=True)
    logo_16x16 = models.ImageField(upload_to='img/studio', blank=True, null=True)

    def __unicode__(self):
        return self.title

