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
    timestamp = models.DateTimeField()
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
            
    def save(self, *args, **kwargs):
        if not self.id:
            self.timestamp = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(BandInvitation, self).save(*args, **kwargs)


class SampleFile(models.Model):
    """
    represents the actual data for a sample file.
    """
    # md5 hash of the binary data of the sample
    hex_digest = models.CharField(max_length=32, unique=True)

    # where it is on disk, relative to MEDIA_ROOT
    path = models.CharField(max_length=256)

    def __unicode__(self):
        return self.path

class UploadedSample(models.Model):
    """
    A sample that a user has uploaded for a band. Links to a SampleFile.
    """
    # the file title of the dependency. it may contain path 
    # separators in the form of forward slashes.
    title = models.CharField(max_length=512)

    # link to the sample file. null if the link is unresolved.
    sample_file = models.ForeignKey(SampleFile)
    
    # who uploaded the sample
    user = models.ForeignKey(User, null=True, blank=True)

    # for what band was the sample uploaded
    band = models.ForeignKey('main.Band', null=True, blank=True)

    def __unicode__(self):
        return "%s (%s): %s" % (self.user.username, self.band.title, self.title)

class SampleDependency(models.Model):
    """
    Represents the title of a sample, used in a song.
    Links to an UploadedSample if it is resolved.
    """
    # the file title of the dependency. it may contain path 
    # separators in the form of forward slashes.
    title = models.CharField(max_length=512)

    # link to the UploadedSample, null if unresolved
    uploaded_sample = models.ForeignKey('UploadedSample', null=True, blank=True)

    # what song uses the dependency
    song = models.ForeignKey('main.Song')

    def __unicode__(self):
        if self.uploaded_sample is None:
            resolution = "not resolved"
        else:
            resolution = "resolved"
        return "%s (%s)" % (self.title, resolution)

class PluginDepenency(models.Model):
    GENERATOR, EFFECT = range(2)

    PLUGIN_TYPE_CHOICES = (
        (GENERATOR, 'Generator'),
        (EFFECT, 'Effect'),
    )

    plugin_type = models.IntegerField(choices=PLUGIN_TYPE_CHOICES)

    # the name of the plugin. this identifies it.
    title = models.CharField(max_length=256, unique=True)

    # identifier string to use in urls. same as title except safe.
    url = models.CharField(max_length=100, unique=True)

    # best link to download or buy the plugin
    external_url = models.CharField(max_length=500, null=True, blank=True)

    # price, to the best of our knowledge. if it's free it means external_url
    # is as close to a download link as we can get.
    price = models.FloatField(null=True, blank=True)

    # if this plugin automatically comes with a studio, this links to that studio
    comes_with_studio = models.ForeignKey('Studio', null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.url is None:
            self.url = create_url(self.title, lambda proposed: PluginDepenency.objects.filter(url=proposed).count() > 0)
        if self.comes_with_studio is not None:
            self.associate_with_studio(self.comes_with_studio)
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(PluginDepenency, self).save(*args, **kwargs)

    def associate_with_studio(self, studio):
        self.comes_with_studio = studio
        # every user that has studio should be marked as having self
        for profile in Profile.objects.filter(studios=studio):
            profile.plugins.add(self)
            profile.save()

    def __unicode__(self):
        return self.title

class ProjectVersion(models.Model):
    project = models.ForeignKey('Project')
    # comments, title, owner, and timestamp are in the song
    song = models.ForeignKey(Song)
    # version counter like subversion
    version = models.IntegerField()

    # when we save, update the Project's cache
    def saveNewVersion(self, *args, **kwargs):
        self.project.title = self.song.title
        if not self.id:
            self._save(*args, **kwargs)
        self.project.latest_version = self
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(ProjectVersion, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s version %i" % (self.song.title, self.version)

class Project(models.Model):
    # title is simply a cache of the latest version's song's title
    title = models.CharField(max_length=100, null=True, blank=True)
    # latest_version is a cache of the latest version
    latest_version = models.ForeignKey('ProjectVersion', null=True, blank=True, related_name='latest_version')

    band = models.ForeignKey(Band)
    date_activity = models.DateTimeField()

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
        if self.title is not None:
            return self.title

        return "error: title not cached"

    def save(self, *args, **kwargs):
        self.date_activity = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(Project, self).save(*args, **kwargs)

class Studio(models.Model):
    # e.g. FL Studio
    title = models.CharField(max_length=100)

    # studio identifier, also used as the url
    identifier = models.CharField(max_length=50, unique=True)

    # url to get to the studio's website
    external_url = models.CharField(max_length=500, unique=True, null=True, blank=True)

    # best estimate of how much it costs
    price = models.FloatField(null=True, blank=True)

    # capabilities - what we can do with the studio
    # whether we have dependency support
    canReadFile = models.BooleanField()
    # whether we can merge two project files
    canMerge = models.BooleanField()
    # whether we can render a project on the server
    canRender = models.BooleanField()

    # description for info page
    info = models.TextField(blank=True)

    logo_large = models.ImageField(upload_to='img/studio', blank=True, null=True, max_length=512)
    logo_16x16 = models.ImageField(upload_to='img/studio', blank=True, null=True, max_length=512)

    def __unicode__(self):
        return self.title

