from django.db import models
from django.contrib.auth.models import User
from chat.models import ChatRoom

class Band(models.Model):
    title = models.CharField(max_length=100)

    def __unicode__(self):
        return self.title

class Profile(models.Model):
    UNSAFE_KEYS = (
        'activate_code',
        'activated',
        'competitions_bookmarked',
    )

    user = models.ForeignKey(User, unique=True)
    solo_band = models.ForeignKey(Band)
    activated = models.BooleanField()
    activate_code = models.CharField(max_length=256)
    date_activity = models.DateTimeField(auto_now=True)

    # the competitions the player has bookmarked
    competitions_bookmarked = models.ManyToManyField('Competition', blank=True, related_name='competitions_bookmarked')

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
    host = models.ForeignKey(User)

    # optional
    theme = models.TextField(blank=True)
    # can entrants view the theme before it starts?
    preview_theme = models.BooleanField()

    # optional
    rules = models.TextField(blank=True)
    # can entrants view the rules before it starts?
    preview_rules = models.BooleanField()

    # when this competition was created
    date_created = models.DateTimeField(auto_now_add=True)

    # when the theme is announced / when the competition starts
    start_date = models.DateTimeField()

    # deadline for submitting entries
    submit_deadline = models.DateTimeField()

    have_listening_party = models.BooleanField()
    # must be after submit_deadline, with enough time for
    # processing.
    listening_party_start_date = models.DateTimeField(blank=True, null=True)

    # this date is unknown until all entries are submitted and the
    # processing is complete
    listening_party_end_date = models.DateTimeField(blank=True, null=True)

    # deadline for casting votes. must be after listening party end time,
    # which is undetermined. People must have at least 10 minutes to vote,
    # so when the processing from the submit_deadline is finished, it will
    # recalculate this value based on the then-known listening_party_end_date
    vote_deadline = models.DateTimeField(blank=True, null=True)

    # length of the voting period in seconds. Used to calculate vote_deadline
    # after listening party end date is computed.
    vote_period_length = models.IntegerField()

    # one chat room per competition
    chat_room = models.ForeignKey(ChatRoom, blank=True, null=True)

    def __unicode__(self):
        return "%s on %s" % (self.title, self.start_date)

class ThumbsUp(models.Model):
    """
    A ThumbsUp is something a user gives to a competition entry.
    """

    owner = models.ForeignKey(User)
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
    owner = models.ForeignKey(User) # who uploaded it
    band = models.ForeignKey(Band) # who this song is attributed to
    title = models.CharField(max_length=100)
    # length in seconds, grabbed from mp3_file metadata
    length = models.FloatField()

    # author comments
    comments = models.TextField(blank=True)

    date_added = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s - %s" % (self.owner, self.title)

class Entry(models.Model):
    """
    An entrant submits an Entry to a Competition.
    """
    competition = models.ForeignKey(Competition)
    owner = models.ForeignKey(User)
    song = models.ForeignKey(Song)
    submit_date = models.DateTimeField(auto_now_add=True)
    edit_date = models.DateTimeField(auto_now=True)

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

    owner = models.ForeignKey(User)
    content = models.TextField()

    def __unicode__(self):
        return "%s - %" % (owner, content[:30])
    

class Tag(models.Model):
    title = models.CharField(max_length=30)

    def __unicode__(self):
        return self.title
