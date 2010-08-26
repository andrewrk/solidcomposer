from base.models import SerializableModel, create_url
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
import main.models

class BandInvitation(SerializableModel):
    """
    An invitation from a user to join their band. It can be a code, which is
    redeemed by hyperlink, or a direct invitation.
    """

    PUBLIC_ATTRS = (
        'inviter',
        'band',
        'timestamp',
        'role',
        'expire_date',
    )

    OWNER_ATTRS = (
        'count',
        'invitee',
    )

    # who sent the invite
    inviter = models.ForeignKey(User, related_name="inviter")
    band = models.ForeignKey('main.Band')
    timestamp = models.DateTimeField()
    role = models.IntegerField(choices=main.models.BandMember.ROLE_CHOICES, default=main.models.BandMember.BAND_MEMBER)

    # when the invite becomes inactive. null means never
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
        "returns the hyperlink you can use to redeem this invitation."
        if self.code is None:
            return None
        else:
            from django.core.urlresolvers import reverse
            from django.contrib.sites.models import Site
            current_site = Site.objects.get_current()
            return 'http://' + current_site.domain + reverse('workbench.redeem_invitation', args=[self.code])
            
    def save(self, *args, **kwargs):
        if not self.id:
            self.timestamp = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(BandInvitation, self).save(*args, **kwargs)
    
    def __unicode__(self):
        if self.isLink():
            return "URL from {0} to join {1}".format(self.inviter.username, self.band.title)
        else:
            return "{0} inviting {1} to join {2}".format(self.inviter.username, self.invitee.username, self.band.title)


class SampleFile(SerializableModel):
    """
    represents the actual data for a sample file.
    """
    PUBLIC_ATTRS = (
        'hex_digest',
        'path',
    )

    # md5 hash of the binary data of the sample
    hex_digest = models.CharField(max_length=32, unique=True)

    # where it is on disk, relative to MEDIA_ROOT
    path = models.CharField(max_length=256)

    # low-kbps preview in mp3 format. null if not done yet.
    mp3_preview = models.CharField(max_length=256, blank=True, null=True)

    def __unicode__(self):
        return self.path

class UploadedSample(SerializableModel):
    """
    A sample that a user has uploaded for a band. Links to a SampleFile.
    """

    PUBLIC_ATTRS = (
        'title',
        'user',
        'band',
    )

    OWNER_ATTRS = (
        'sample_file',
    )

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

class SampleDependency(SerializableModel):
    """
    Represents the title of a sample, used in a song.
    Links to an UploadedSample if it is resolved.
    """

    PUBLIC_ATTRS = (
        'title',
        'uploaded_sample',
        'song',
    )

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

class PluginDepenency(SerializableModel):
    # studio is only used when talking about users having or not having
    # dependencies.
    GENERATOR, EFFECT, STUDIO = range(3)

    PLUGIN_TYPE_CHOICES = (
        (GENERATOR, 'Generator'),
        (EFFECT, 'Effect'),
    )

    PUBLIC_ATTRS = (
        'plugin_type',
        'title',
        'url',
        'external_url',
        'price',
        'comes_with_studio',
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

    # markdown format text to display on the plugin page
    info = models.TextField(blank=True)

    # display this on the plugin page
    screenshot = models.ImageField(upload_to='img/studio', blank=True, null=True, max_length=512)

    def save(self, *args, **kwargs):
        if not self.url:
            self.url = create_url(self.title, lambda proposed: PluginDepenency.objects.filter(url=proposed).count() == 0)
        if self.comes_with_studio is not None:
            self.associate_with_studio(self.comes_with_studio)
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(PluginDepenency, self).save(*args, **kwargs)

    def associate_with_studio(self, studio):
        self.comes_with_studio = studio
        # every user that has studio should be marked as having self
        for profile in main.models.Profile.objects.filter(studios=studio):
            profile.plugins.add(self)
            profile.save()

    def __unicode__(self):
        return self.title

class ProjectVersion(SerializableModel):
    PUBLIC_ATTRS = (
        'project',
        'owner',
        'comment_node',
        'date_added',
        'song',
        'version',
        'new_title',
        'old_title',
        'provided_samples',
    )

    project = models.ForeignKey('Project')

    # we duplicate fields from song because we might have a version without one.
    owner = models.ForeignKey(User, null=True, blank=True)
    comment_node = models.ForeignKey('main.SongCommentNode', null=True, blank=True)
    date_added = models.DateTimeField()

    # if it's not null then this is a legit new song version.
    song = models.ForeignKey('main.Song', null=True, blank=True)
    # version counter like subversion.
    # only increments when it is a song version.
    version = models.IntegerField()

    # if it's not blank then this is a rename.
    new_title = models.CharField(max_length=100, blank=True, default='')
    old_title = models.CharField(max_length=100, blank=True, default='')

    # if it's not null then this is a version to provide samples
    provided_samples = models.ManyToManyField('UploadedSample', blank=True, related_name='provided_samples')

    # when we save, update the Project's cache
    def saveNewVersion(self, *args, **kwargs):
        """
        Use this function to save when you are using a song as the new version.
        """
        self.owner = self.song.owner
        self.date_added = self.song.date_added
        self.comment_node = self.song.comment_node

        self.project.title = self.song.title
        if not self.id:
            self._save(*args, **kwargs)

        self.project.latest_version = self
        self.project.save()
        self._save(*args, **kwargs)
        self.makeLogEntry()

    def makeLogEntry(self):
        if self.song is not None:
            if self.version == 1:
                self.createNewProjectLogEntry()
            else:
                self.createNewVersionLogEntry()
        elif self.new_title != '':
            self.createRenameLogEntry()
        elif self.provided_samples.count() > 0:
            self.createUploadSamplesLogEntry()

    def save(self, *args, **kwargs):
        if not self.id:
            self.date_added = datetime.now()
            self._save(*args, **kwargs)
            self.makeLogEntry()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(ProjectVersion, self).save(*args, **kwargs)

    def createNewProjectLogEntry(self):
        "create log entry for new project"
        entry = LogEntry()
        entry.entry_type = LogEntry.NEW_PROJECT
        entry.band = self.project.band
        entry.catalyst = self.owner
        entry.version = self
        entry.save()

    def createRenameLogEntry(self):
        entry = LogEntry()
        entry.entry_type = LogEntry.SONG_RENAMED
        entry.band = self.project.band
        entry.catalyst = self.owner
        entry.version = self
        entry.save()

    def createUploadSamplesLogEntry(self):
        entry = LogEntry()
        entry.entry_type = LogEntry.SAMPLES_UPLOADED
        entry.band = self.project.band
        entry.catalyst = self.owner
        entry.version = self
        entry.save()

    def createNewVersionLogEntry(self):
        entry = LogEntry()
        entry.entry_type = LogEntry.SONG_CHECKED_IN
        entry.band = self.project.band
        entry.catalyst = self.owner
        entry.version = self
        entry.save()

    def __unicode__(self):
        if self.song is not None:
            return "%s version %i" % (self.song.title, self.version)
        elif self.new_title != '':
            return "Rename to %s" % self.new_title
        elif self.provided_samples.count() > 0:
            return "Version to provide samples."
        else:
            return "Invalid null version."

class Project(SerializableModel):
    PUBLIC_ATTRS = (
        'title',
        'latest_version',
        'band',
        'date_activity',
        'date_checked_out',
        'checked_out_to',
        'visible',
        'forked_from',
        'merged_from',
        'tags',
        'scrap_voters',
        'promote_voters',
        'subscribers',
    )

    # title is simply a cache of the latest version's song's title
    title = models.CharField(max_length=100, null=True, blank=True)
    # latest_version is a cache of the latest version
    latest_version = models.ForeignKey('ProjectVersion', null=True, blank=True, related_name='latest_version')

    band = models.ForeignKey('main.Band')
    date_activity = models.DateTimeField()

    # who has it checked out, null if nobody
    checked_out_to = models.ForeignKey(User, null=True, blank=True, related_name='checked_out_to')
    date_checked_out = models.DateTimeField(null=True, blank=True)

    # False if scrapped
    visible = models.BooleanField(default=True)

    # if this project is a fork, what projectversion is it forked from?
    forked_from = models.ForeignKey('ProjectVersion', null=True, blank=True, related_name='forked_from')
    merged_from = models.ManyToManyField('ProjectVersion', null=True, blank=True, related_name='merged_from')

    tags = models.ManyToManyField('main.Tag', blank=True)

    scrap_voters = models.ManyToManyField(User, blank=True, related_name='scrap_voters')
    promote_voters = models.ManyToManyField(User, blank=True, related_name='promote_voters')
    subscribers = models.ManyToManyField(User, blank=True, related_name='project_subscribers')

    def __unicode__(self):
        if self.title is not None:
            return self.title

        return "error: title not cached"

    def save(self, *args, **kwargs):
        self.date_activity = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(Project, self).save(*args, **kwargs)

class Studio(SerializableModel):
    PUBLIC_ATTRS = (
        'title',
        'identifier',
        'external_url',
        'price',
        'canReadFile',
        'canMerge',
        'canRender',
        'logo_large',
        'logo_16x16',
    )


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

class LogEntry(SerializableModel):
    """
    Something that happened that is relevant to a band. We use this to have a Recent Events pane in workbench.
    """

    SONG_CRITIQUE, SONG_CHECKED_IN, SONG_CHECKED_OUT, SAMPLES_UPLOADED, \
        SONG_RENAMED, POKE, BAND_MEMBER_JOIN, BAND_MEMBER_QUIT, NEW_PROJECT, \
        SONG_JUST_CHECK_IN, SPACE_ALLOCATED_CHANGE = range(11)

    ENTRY_TYPE_CHOICES = (
        (SONG_CRITIQUE, 'Song critique'),
        (SONG_CHECKED_IN, 'Song checked in'),
        (SONG_CHECKED_OUT, 'Song checked out'),
        (SAMPLES_UPLOADED, 'Samples uploaded'),
        (SONG_RENAMED, 'Song renamed'),
        (POKE, 'Someone got poked'),
        (BAND_MEMBER_JOIN, 'Band member joined'),
        (BAND_MEMBER_QUIT, 'Band member quit'),
        (NEW_PROJECT, 'New project'),
        (SONG_JUST_CHECK_IN, 'Just check in'),
        (SPACE_ALLOCATED_CHANGE, 'Space allocated change'),
    )

    PUBLIC_ATTRS = (
        'entry_type',
        'timestamp',
        'band',
        'catalyst',
        'target',
        'node',
        'version',
        'project',
        'old_amount',
        'new_amount',
    )

    entry_type = models.IntegerField(choices=ENTRY_TYPE_CHOICES)
    timestamp = models.DateTimeField()

    # the band that this is relevant to.
    band = models.ForeignKey('main.Band')

    # the person who caused the action
    catalyst = models.ForeignKey(User, null=True, blank=True, related_name="catalyst")

    # who is the action directed at? for example the person being poked.
    target = models.ForeignKey(User, null=True, blank=True, related_name="target")

    # the comment node for a song critique
    node = models.ForeignKey('main.SongCommentNode', null=True, blank=True)

    # the project version for when a project is updated
    version = models.ForeignKey('ProjectVersion', null=True, blank=True)

    # the project for when a project is just checked in
    project = models.ForeignKey('Project', null=True, blank=True)

    # the amount of space donated changed
    old_amount = models.BigIntegerField(default=0)
    new_amount = models.BigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.id:
            self.timestamp = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(LogEntry, self).save(*args, **kwargs)

