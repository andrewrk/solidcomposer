from django.db import models
from django.contrib.auth.models import User
from competitions.models import ThumbsUp

from datetime import datetime, timedelta
import string

import os
from django.conf import settings

FULL_OPEN, OPEN_SOURCE, TRANSPARENT, NO_CRITIQUE, PRIVATE = range(5)

MANAGER, BAND_MEMBER, CRITIC, FAN, BANNED = range(5)
ROLE_CHOICES = (
    (MANAGER, 'Manager'), # full privileges
    (BAND_MEMBER, 'Band member'), # full privileges except band admin
    (CRITIC, 'Critic'), # can view and post comments in project manager
    (FAN, 'Fan'), # regular site user
    (BANNED, 'Banned'), # this person is blacklisted
)

def create_url(title, is_unique=None):
    """
    creates a clean and safe url to use based on a name.
    calls is_unique with a candidate to see if it is unique.
    """
    allowed_chars = string.letters + string.digits + r'_-.'
    replacement = '_'

    # break title into url safe string
    safe_title = ''
    for c in title:
        if c in allowed_chars:
            safe_title += c
        else:
            safe_title += replacement

    if is_unique is None:
        return safe_title

    # append digits until it is unique
    suffix = 2
    proposed = safe_title
    while not is_unique(proposed):
        proposed = safe_title + str(suffix)
        suffix += 1

    return proposed

class BandMember(models.Model):
    user = models.ForeignKey(User)
    band = models.ForeignKey('Band')
    role = models.IntegerField(choices=ROLE_CHOICES, default=MANAGER)

    def __unicode__(self):
        return u'%s - %s: %s' % (str(self.band), dict(ROLE_CHOICES)[self.role], str(self.user))

class Band(models.Model):
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
        self.url = create_url(self.title, lambda proposed: Band.objects.filter(url=proposed).count() > 0)

    def rename(self, new_name):
        self.title = new_name
        self.create_url()

    def permission_to_work(self, user):
        "Returns whether a user can check out and check in projects."
        if not user.is_authenticated():
            return False

        # get the BandMember for this user
        members = BandMember.objects.filter(user=user, band=self)
        if members.count() != 1:
            # not in this band. if the band is FULL_OPEN they can edit.
            return self.openness == FULL_OPEN

        member = members[0]
        return member.role in (MANAGER, BAND_MEMBER)

    def __unicode__(self):
        return self.title


class AccountPlan(models.Model):
    """
    The payment plan and features that a user has
    """
    title = models.CharField(max_length=50)
    # how much the user has to pay per month
    usd_per_month = models.FloatField()
    # byte count limit of their account
    total_space = models.BigIntegerField()
    # how many bands can they make
    band_count_limit = models.IntegerField()

    def __unicode__(self):
        return "%s - $%s/mo" % (self.title, self.usd_per_month)


class Profile(models.Model):
    UNSAFE_KEYS = (
        'activate_code',
        'activated',
        'competitions_bookmarked',
        'plan',
        'total_space',
        'used_space',
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
    # how much space does the user have in their account in bytes
    # the actual accounting is done in Band. this field is simply where purchased bytes
    # are accumulated, which are then doled out to one or more Bands' total_space
    purchased_bytes = models.BigIntegerField(default=0)
    usd_per_month = models.FloatField(default=0.0)
    # how many bands can the user create
    band_count_limit = models.IntegerField(default=1)
    # the string that identifies a customer with the merchant
    customer_id = models.CharField(max_length=256, blank=True)

    # the plugins that the user owns
    plugins = models.ManyToManyField('workshop.PluginDepenency', blank=True, related_name='profile_plugins')

    # the studios that the user owns
    studios = models.ManyToManyField('workshop.Studio', blank=True, related_name='profile_studios')

    # user controlled settings
    # if a user uploads a project with a plugin, do we assume they own it?
    assume_uploaded_plugins_owned = models.BooleanField(default=True)

    def __unicode__(self):
        return self.user.username

    def own_studio(self, studio):
        self.studios.add(studio)
        self.plugins.add(PluginDepenency.objects.filter(comes_with_studio=studio))

    def disown_studio(self, studio):
        self.studios.remove(studio)
        self.plugins.remove(PluginDepenency.objects.filter(comes_with_studio=studio))

    def get_points(self):
        return ThumbsUp.objects.filter(entry__owner=self).count()

    def save(self, *args, **kwargs):
        "Update auto-populated fields before saving"
        self.date_activity = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        "Save without any auto field population"
        super(Profile, self).save(*args, **kwargs)

    disallowed_chars = r'\./?'

class Song(models.Model):
    # filename where mp3 can be found
    mp3_file = models.CharField(max_length=500, null=True, blank=True)

    # in case the artist was generous enough to provide source
    source_file = models.CharField(max_length=500, blank=True)
    studio = models.ForeignKey('workshop.Studio', null=True, blank=True)

    # filename where generated waveform img can be found
    waveform_img = models.CharField(max_length=500, blank=True)

    # track data
    owner = models.ForeignKey(User) # who uploaded it
    band = models.ForeignKey(Band) # who this song is attributed to
    title = models.CharField(max_length=100)
    album = models.CharField(max_length=100, null=True, blank=True)
    # length in seconds, grabbed from mp3_file metadata
    length = models.FloatField()

    # author comments
    comments = models.TextField(blank=True)

    date_added = models.DateTimeField()

    # dependencies
    plugins = models.ManyToManyField('workshop.PluginDepenency', blank=True, related_name='song_plugins')

    def __unicode__(self):
        return self.displayString()

    def permission_to_view_source(self, user):
        "Returns whether a user can download the project file and samples of the song."
        return self.band.permission_to_work(user) # TODO: or self.is_open_source 

    def displayString(self):
        """
        returns a string fit for representing this song
        """
        if self.album is None:
            return "%s - %s" % (self.band.title, self.title)
        else:
            return "%s - %s (%s)" % (self.band.title, self.title, self.album)

    def save(self, *args, **kwargs):
        "Update auto-populated fields before saving"
        if not self.id:
            self.date_added = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        "Save without any auto field population"
        super(Song, self).save(*args, **kwargs)

class SongCommentThread(models.Model):
    """
    A thread, which contains comments about a particular position
    in the Song.
    """
    song = models.ForeignKey('Song')

    # how many seconds into the song the comment was made.
    # null indicates no particular position
    position = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return "%s at position %s" % (entry, position)

class SongComment(models.Model):
    """
    A comment in a SongCommentThread
    """
    date_created = models.DateTimeField()
    date_edited = models.DateTimeField()

    owner = models.ForeignKey(User)
    content = models.TextField()

    def __unicode__(self):
        return "%s - %" % (owner, content[:30])
        
    def save(self, *args, **kwargs):
        self.date_edited = datetime.now()
        if not self.id:
            self.date_created = self.date_edited
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(SongComment, self).save(*args, **kwargs)
    

class Tag(models.Model):
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
        
