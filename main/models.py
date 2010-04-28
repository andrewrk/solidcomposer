from django.db import models
from django.contrib.auth.models import User

SYSTEM, ACTION, MESSAGE, JOIN, LEAVE, NOTICE = range(6)
OPEN, WHITELIST, BLACKLIST = range(3)

class Profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    artist_name = models.CharField(max_length=256)
    activated = models.BooleanField()
    activate_code = models.CharField(max_length=256)
    date_activity = models.DateTimeField(auto_now=True)
    logon_count = models.IntegerField()

    # the competitions the player has bookmarked
    competitions_bookmarked = models.ManyToManyField('Competition', blank=True, related_name='competitions_bookmarked')

    UNSAFE_KEYS = (
        'activate_code',
        'activated',
    )

    def __unicode__(self):
        return self.user.username

    def get_points(self):
        return ThumbsUp.objects.filter(entry__owner=self).count()

class Competition(models.Model):
    UNSAFE_KEYS = (
        'theme', # can only see theme if preview_theme
        'rules', # can only see rules if preview_rules
    )

    title = models.CharField(max_length=256)

    # who created the competition
    host = models.ForeignKey(Profile)

    # optional
    theme = models.TextField(blank=True)
    # can entrants view the theme before it starts?
    preview_theme = models.BooleanField()

    # optional
    rules = models.TextField(blank=True)
    # can entrants view the rules before it starts?
    preview_rules = models.BooleanField()

    have_listening_party = models.BooleanField()
    # must be after submit_deadline, with enough time for
    # processing.
    listening_party_start_date = models.DateTimeField(blank=True, null=True)

    # this date is unknown until all entries are submitted and the
    # processing is complete
    listening_party_end_date = models.DateTimeField(blank=True, null=True)

    # when this competition was created
    date_created = models.DateTimeField(auto_now_add=True)

    # when the theme is announced / when the competition starts
    start_date = models.DateTimeField()

    # deadline for submitting entries
    submit_deadline = models.DateTimeField()

    # deadline for casting votes. must be after listening party end time,
    # which is undetermined. People must have at least 10 minutes to vote,
    # so when the processing from the submit_deadline is finished, it will
    # recalculate this value based on the then-known listening_party_end_date
    vote_deadline = models.DateTimeField(blank=True, null=True)

    # length of the voting period in seconds. Used to calculate vote_deadline
    # after listening party end date is computed.
    vote_period_length = models.IntegerField()

    # one chat room per competition
    chat_room = models.ForeignKey('ChatRoom', blank=True, null=True)

    def __unicode__(self):
        return "%s on %s" % (self.title, self.start_date)

class ThumbsUp(models.Model):
    """
    A ThumbsUp is something a user gives to a competition entry.
    """

    owner = models.ForeignKey(Profile)
    entry = models.ForeignKey('Entry')
    date_given = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s gives +1 to %s on %s" % (self.owner, self.entry, self.date_given)

class Song(models.Model):
    # filename where mp3 can be found
    mp3_file = models.CharField(max_length=500)

    # in case the artist was generous enough to provide source
    source_file = models.CharField(max_length=500, blank=True)

    # filename where generated waveform img can be found
    waveform_img = models.CharField(max_length=500, blank=True)

    # track data
    owner = models.ForeignKey('Profile')
    title = models.CharField(max_length=100)
    # length in seconds, grabbed from mp3_file metadata
    length = models.FloatField()

    date_added = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s - %s" % (self.owner, self.title)

class Entry(models.Model):
    """
    An entrant submits an Entry to a Competition.
    """
    competition = models.ForeignKey(Competition)
    owner = models.ForeignKey(Profile)
    song = models.ForeignKey(Song)
    submit_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s in %s" % (self.song, self.competition)

class SongCommentThread(models.Model):
    """
    A thread, which contains comments about a particular position
    in the Song.
    """

    entry = models.ForeignKey('Entry')

    # position in the song the comment was made.
    # negative number indicates no particular position
    position = models.FloatField()

    def __unicode__(self):
        return "%s at position %s" % (entry, position)

class SongComment(models.Model):
    """
    A comment in a SongCommentThread
    """
    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(Profile)
    content = models.TextField()

    def __unicode__(self):
        return "%s - %" % (owner, content[:30])
    
class ChatRoom(models.Model):
    """
    ChatRoom contains ChatMessages and manages who is allowed to be in it.
    """
    PERMISSION_TYPES = (
        (OPEN, 'open'),
        (WHITELIST, 'whitelist'),
        (BLACKLIST, 'blacklist'),
    )

    UNSAFE_KEYS = (
        'whitelist',
        'blacklist',
    )

    permission_type = models.IntegerField(choices=PERMISSION_TYPES)
    whitelist = models.ManyToManyField('Profile', null=True, blank=True, related_name="whitelisted_users")
    blacklist = models.ManyToManyField('Profile', null=True, blank=True, related_name="blacklisted_users")

    # the date that chat becomes active. null means no bound
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return "ChatRoom %i" % self.id

class ChatMessage(models.Model):
    """
    A message that belongs to a ChatRoom
    """

    MESSAGE_TYPES = (
        (SYSTEM, 'system'),
        (ACTION, 'action'),
        (MESSAGE, 'message'),
        (JOIN, 'join'),
        (LEAVE, 'leave'),
        (NOTICE, 'notice'),
    )

    room = models.ForeignKey('ChatRoom')
    type = models.IntegerField(choices=MESSAGE_TYPES)
    author = models.ForeignKey('Profile', blank=True, null=True)
    message = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        """
        Each message type has a special representation, return
        that representation.
        """
        if self.type == SYSTEM:
            return u'SYSTEM: %s' % self.message[:30]
        if self.type == NOTIFICATION:
            return u'NOTIFICATION: %s' % self.message[:30]
        elif self.type == JOIN:
            return 'JOIN: %s' % self.author
        elif self.type == LEAVE:
            return 'LEAVE: %s' % self.author
        elif self.type == ACTION:
            return 'ACTION: %s > %s' % (self.author, self.message[:30])
        return self.message[:30]

class Appearance(models.Model):
    """
    An Appearance tracks when a person was seen in a ChatRoom.
    """
    person = models.ForeignKey('Profile')
    room = models.ForeignKey('ChatRoom')
    timestamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s in %s on %s" % (self.person, self.room, self.timestamp)
