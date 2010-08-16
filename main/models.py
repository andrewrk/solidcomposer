from base.models import SerializableModel, create_url
from competitions.models import ThumbsUp
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import models
from main import design
import workshop
import hashlib

class BandMember(SerializableModel):
    MANAGER, BAND_MEMBER, CRITIC, FAN, BANNED = range(5)
    ROLE_CHOICES = (
        (MANAGER, 'Manager'), # full privileges
        (BAND_MEMBER, 'Band member'), # full privileges except band admin
        (CRITIC, 'Critic'), # can view and post comments in project manager
        (FAN, 'Fan'), # regular site user
        (BANNED, 'Banned'), # this person is blacklisted
    )

    PUBLIC_ATTRS = (
        'user',
        'band',
        'role',
    )

    OWNER_ATTRS = (
        'space_donated',
    )

    user = models.ForeignKey(User)
    band = models.ForeignKey('main.Band')
    role = models.IntegerField(choices=ROLE_CHOICES, default=MANAGER)
    space_donated = models.IntegerField(default=0)

    def __unicode__(self):
        return u'%s - %s: %s' % (str(self.band), dict(BandMember.ROLE_CHOICES)[self.role], str(self.user))


class Band(SerializableModel):
    FULL_OPEN, OPEN_SOURCE, TRANSPARENT, NO_CRITIQUE, PRIVATE = range(5)
    OPENNESS_CHOICES = (
        # completely open. anyone with an account and not banned can contribute.
        (FULL_OPEN, 'Fully open'),
        # open source but only band members can contribute
        (OPEN_SOURCE, 'Open source'),
        # anyone can critique (view and post comments in project manager)
        # but source is protected
        (TRANSPARENT, 'Transparent'),
        # anyone can view and listen to projects but feedback is locked
        (NO_CRITIQUE, 'Critiquing disabled'),
        # private band, the public can only see what the band releases
        (PRIVATE, 'Private'),
    )

    PUBLIC_ATTRS = (
        'title',
        'url',
        'openness',
        'bio',
    )
    OWNER_ATTRS = (
        'concurrent_editing',
        'total_space',
        'used_space',
    )

    # if you want to change the title, you need to do band.rename(new_title)
    title = models.CharField(max_length=100)
    # automatically created. as close to title as possible yet unique and
    # file system safe.
    url = models.CharField(max_length=110, unique=True, null=True)

    # openness is what applies to people who aren't explicitly in the 
    # band members list.
    openness = models.IntegerField(choices=OPENNESS_CHOICES, default=PRIVATE)

    # band information
    bio = models.TextField(blank=True, null=True)

    # True if people have to check stuff out to work on it
    concurrent_editing = models.BooleanField(default=False)

    # how much space does the band have in their account in bytes
    # users can dole out their total_space to a band.
    # the default should be the total_space from the free plan in the database.
    total_space = models.BigIntegerField()
    used_space = models.BigIntegerField(default=0)
    # how long has it been since used_space > total_space
    abandon_date = models.DateTimeField(blank=True, null=True)

    def isReadOnly(self):
        return self.used_space > self.total_space

    def save(self, *args, **kwargs):
        if self.used_space > self.total_space and self.abandon_date is None:
            self.abandon_date = datetime.now()
        elif self.used_space <= self.total_space and self.abandon_date is not None:
            self.abandon_date = None

        if self.url is None:
            self.create_url()

        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(Band, self).save(*args, **kwargs)

    def create_url(self):
        self.url = create_url(self.title, lambda proposed: Band.objects.filter(url=proposed).count() == 0)

    def rename(self, new_name):
        self.title = new_name
        self.create_url()

    def permission_to_view_source(self, user):
        "Returns whether a user can view samples and project file for the band."
        if self.openness == Band.FULL_OPEN:
            return True

        return self.permission_to_work(user)

    def permission_to_work(self, user):
        "Returns whether a user can check out and check in projects."
        if not user.is_authenticated():
            return False

        if self.openness == Band.FULL_OPEN:
            return True

        # get the BandMember for this user
        try:
            member = BandMember.objects.get(user=user, band=self)
        except BandMember.DoesNotExist:
            return False

        return member.role in (BandMember.MANAGER, BandMember.BAND_MEMBER)

    def permission_to_critique(self, user):
        if not user.is_authenticated():
            return False

        if self.openness in (Band.FULL_OPEN, Band.OPEN_SOURCE, Band.TRANSPARENT):
            return True

        # get the BandMember for this user
        try:
            member = BandMember.objects.get(user=user, band=self)
        except BandMember.DoesNotExist:
            return False

        return member.role in (BandMember.MANAGER, BandMember.BAND_MEMBER, BandMember.CRITIC)

    def permission_to_invite(self, user):
        if not user.is_authenticated():
            return False

        if self.openness == Band.FULL_OPEN:
            return True

        # get the BandMember for this user
        try:
            member = BandMember.objects.get(user=user, band=self)
        except BandMember.DoesNotExist:
            return False

        return member.role == BandMember.MANAGER

    def __unicode__(self):
        return self.title


class AccountPlan(SerializableModel):
    """
    The payment plan and features that a user has
    """

    PUBLIC_ATTRS = (
        'title',
        'usd_per_month',
        'total_space',
        'band_count_limit',
    )

    title = models.CharField(max_length=50)
    # how much the user has to pay per month
    usd_per_month = models.FloatField()
    # byte count limit of their account
    total_space = models.BigIntegerField()
    # how many bands can they make
    band_count_limit = models.IntegerField()

    def __unicode__(self):
        return "%s - $%s/mo" % (self.title, self.usd_per_month)


class Profile(SerializableModel):
    PUBLIC_ATTRS = (
        'user',
        'solo_band',
        'date_activity',
        'bio',
    )
    OWNER_ATTRS = (
        'activated',
        'competitions_bookmarked',
        'plan',
        'purchased_bytes',
        'usd_per_month',
        'band_count_limit',
        'plugins',
        'studios',
        'assume_uploaded_plugins_owned',
    )
    user = models.ForeignKey(User, unique=True)
    solo_band = models.ForeignKey(Band)
    activated = models.BooleanField()
    activate_code = models.CharField(max_length=256)
    date_activity = models.DateTimeField()

    bio = models.TextField(blank=True, null=True)

    # the competitions the player has bookmarked
    competitions_bookmarked = models.ManyToManyField('competitions.Competition', blank=True, related_name='competitions_bookmarked')

    # account stuff. When a user signs up for a plan, this is inherited from
    # the plan's data, but it can be overridden here.
    plan = models.ForeignKey(AccountPlan, blank=True, null=True)
    # how many bands can the user create
    band_count_limit = models.IntegerField(default=1)
    # how much space does the user have in their account in bytes
    # the actual accounting is done in Band. this field is simply where purchased bytes
    # are accumulated, which are then doled out to one or more Bands' total_space
    purchased_bytes = models.BigIntegerField(default=0)

    # billing information
    # if they are on a monthly plan, this field will be greater than 0.
    usd_per_month = models.FloatField(default=0.0)
    # if they are on a pre-paid plan, this will be non-null.
    # when the billing cron job runs, it checks for account_expire_date less than 
    # a month away and bills, adding a month. This means when a person signs up,
    # we bill them immediately and give them 2 months.
    account_expire_date = models.DateTimeField(null=True, blank=True)
    # the string that identifies a customer with the merchant
    customer_id = models.CharField(max_length=256, blank=True)

    # the plugins that the user owns
    plugins = models.ManyToManyField('workshop.PluginDepenency', blank=True, related_name='profile_plugins')

    # the studios that the user owns
    studios = models.ManyToManyField('workshop.Studio', blank=True, related_name='profile_studios')

    # user controlled settings
    # if a user uploads a project with a plugin, do we assume they own it?
    assume_uploaded_plugins_owned = models.BooleanField(default=True)

    # email subscription settings (True means subscribed)
    email_notifications = models.BooleanField(default=True)
    email_newsletter = models.BooleanField(default=True)

    def __unicode__(self):
        return self.user.username

    def own_studio(self, studio):
        self.studios.add(studio)
        self.plugins.add(workshop.models.PluginDepenency.objects.filter(comes_with_studio=studio))

    def disown_studio(self, studio):
        self.studios.remove(studio)
        self.plugins.remove(workshop.models.PluginDepenency.objects.filter(comes_with_studio=studio))

    def get_points(self):
        return ThumbsUp.objects.filter(entry__owner=self).count()

    def save(self, *args, **kwargs):
        "Update auto-populated fields before saving"
        self.date_activity = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        "Save without any auto field population"
        super(Profile, self).save(*args, **kwargs)

    def gravatar_url(self, size):
        return "http://www.gravatar.com/avatar/%s?s=%s&r=pg&d=identicon" % (hashlib.md5(self.user.email).hexdigest(), str(size))

    def gravatar_icon(self):
        return self.gravatar_url(design.gravatar_icon_size)

    def gravatar(self):
        return self.gravatar_url(design.gravatar_large_size)

    def to_dict(self, access=SerializableModel.PUBLIC, chains=[]):
        data = super(Profile, self).to_dict(access, chains)
        # add user data to it
        if access >= SerializableModel.PUBLIC:
            data['username'] = self.user.username
            data['id'] = self.user.id
            data['get_points'] = self.get_points()
            data['gravatar_icon'] = self.gravatar_icon()
            data['gravatar'] = self.gravatar()
        if access >= SerializableModel.OWNER:
            data['email'] = self.user.email
        return data

    def bands_in_count(self):
        "returns how many bands the user is in"
        return BandMember.objects.filter(user=self.user, role__in=(BandMember.BAND_MEMBER,BandMember.MANAGER)).count() 

    def space_used(self):
        return sum([member.space_donated for member in BandMember.objects.filter(user=self.user)])

class Song(SerializableModel):
    PUBLIC_ATTRS = (
        'mp3_file',
        'waveform_img',
        'is_open_source',
        'owner',
        'band',
        'title',
        'album',
        'length',
        'comments',
        'date_added',
        'comment_node',
    )

    OWNER_ATTRS = (
        'source_file',
        'studio',
        'plugins',
    )

    # filename where mp3 can be found
    mp3_file = models.CharField(max_length=500, blank=True)

    # in case the artist was generous enough to provide source
    source_file = models.CharField(max_length=500, blank=True)
    is_open_source = models.BooleanField(default=False)
    is_open_for_comments = models.BooleanField(default=False)
    studio = models.ForeignKey('workshop.Studio', null=True, blank=True)

    # filename where generated waveform img can be found
    waveform_img = models.CharField(max_length=500, blank=True)

    # track data
    owner = models.ForeignKey(User) # who uploaded it
    band = models.ForeignKey(Band) # who this song is attributed to
    title = models.CharField(max_length=100)
    album = models.CharField(max_length=100, blank=True, default="")
    # length in seconds, grabbed from mp3_file metadata
    length = models.FloatField()

    # author comments
    # really should be not null, but we need to save this guy before we can assign it to a comment node's song field.
    comment_node = models.ForeignKey('SongCommentNode', null=True, related_name='song_comment_node')

    date_added = models.DateTimeField()

    # dependencies
    plugins = models.ManyToManyField('workshop.PluginDepenency', blank=True, related_name='song_plugins')

    def __unicode__(self):
        return self.displayString()

    def permission_to_view_source(self, user):
        "Returns whether a user can download the project file and samples of the song."
        return self.is_open_source or self.band.permission_to_view_source(user)

    def permission_to_critique(self, user):
        return self.is_open_source or self.is_open_for_comments or self.band.permission_to_critique(user)

    def displayString(self):
        """
        returns a string fit for representing this song
        """
        if self.album == "":
            return "%s - %s" % (self.band.title, self.title)
        else:
            return "%s - %s (%s)" % (self.band.title, self.title, self.album)

    def save(self, *args, **kwargs):
        if not self.id:
            self.date_added = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(Song, self).save(*args, **kwargs)
    
    def to_dict(self, access=SerializableModel.PUBLIC, chains=[]):
        data = super(Song, self).to_dict(access, chains)
        forwards, new_chains = self.process_chains(chains)
        new_access = self.process_access(access)
        if self.is_open_source:
            data['source_file'] = self.source_file
            if self.studio is not None:
                if 'studio' in forwards:
                    data['studio'] = self.studio.to_dict(new_access, new_chains)
                else:
                    data['studio'] = self.studio.pk
            else:
                data['studio'] = None
            if 'plugins' in forwards:
                data['plugins'] = [obj.to_dict(new_access, new_chains) for obj in self.plugins.all()]
            else:
                data['plugins'] = [obj.pk for obj in self.plugins.all()]
        return data

class SongCommentNode(SerializableModel):
    """
    Contains one comment and a link to its parent.
    If position is not null, then it is a timed comment.
    """
    PUBLIC_ATTRS = (
        'song',
        'parent',
        'date_created',
        'date_edited',
        'owner',
        'content',
        'position',
        'reply_disabled',
        'deleted',
    )

    song = models.ForeignKey('Song', null=True, blank=True)

    # if null then this is the root.
    parent = models.ForeignKey('SongCommentNode', null=True, blank=True)

    date_created = models.DateTimeField()
    date_edited = models.DateTimeField()

    owner = models.ForeignKey(User)
    content = models.TextField(blank=True, max_length=2000)

    # how many seconds into the song the comment was made.
    # null indicates no particular position
    position = models.FloatField(blank=True, null=True)

    # if True, nobody is allowed to reply to this comment.
    reply_disabled = models.BooleanField(default=False)

    # true if the comment is deleted
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        if self.position is None:
            return u"%s: %s" % (self.owner, self.content[:30])
        else:
            return u"%s (%s): %s" % (self.owner, self.position, self.content[:30])

    def to_dict(self, access=SerializableModel.PUBLIC, chains=[]):
        data = super(SongCommentNode, self).to_dict(access, chains)
        if self.deleted:
            del data['content']
        # always follow owner link
        data['owner'] = self.owner.get_profile().to_dict()
        # add the children replies
        data['children'] = [x.to_dict() for x in self.songcommentnode_set.all()]
        return data
        
    def save(self, *args, **kwargs):
        self.date_edited = datetime.now()
        if not self.id:
            self.date_created = self.date_edited

            # create a log entry
            if self.parent != None:
                entry = workshop.models.LogEntry()
                entry.entry_type = workshop.models.LogEntry.SONG_CRITIQUE
                entry.band = self.song.band
                entry.catalyst = self.owner
                entry.node = self
                entry.version = self.song.projectversion_set.all()[0]
                entry.save()

        return self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        return super(SongCommentNode, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # if it's the root node, just set the content to blank.
        if self.parent is None:
            self.content = ""
            self.save()
            return

        # if it's a leaf node, actually delete it
        if self.parent is not None and self.songcommentnode_set.count() == 0:
            return super(SongCommentNode, self).delete(*args, **kwargs)

        # if not, just set delete to true.
        self.deleted = True
        self.save()

class Tag(SerializableModel):
    PUBLIC_ATTRS = (
        'title',
    )

    title = models.CharField(max_length=30)

    def __unicode__(self):
        return self.title

class TempFile(models.Model):
    """
    Represents a temp file sitting on the hard drive that needs to be deleted.
    """
    path = models.CharField(max_length=256)
    death_time = models.DateTimeField(default=datetime.now()+timedelta(hours=3))

    def __unicode__(self):
        return self.path
