from django.db import models
from opensourcemusic.main.models import Profile

class Competition(models.Model):
    title = models.CharField(max_length=256)

    # optional
    theme = models.TextField(null=True, blank=True)
    # can entrants view the theme before it starts?
    preview_theme = models.BooleanField()

    # optional
    rules = models.TextField(null=True, blank=True)
    # can entrants view the rules before it starts?
    preview_rules = models.BooleanField()

    have_listening_party = models.BooleanField()
    # must be after submit_deadline, with enough time for
    # processing.
    listening_party_start_date = models.DateTimeField()

    # this date is unknown until all entries are submitted and the
    # processing is complete
    listening_party_end_date = models.DateTimeField()

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
    vote_deadline = models.DateTimeField()

    # the players that have bookmarked this competition
    players_bookmarked = models.ManyToManyField(Profile, blank=True, related_name='players_bookmarked')

class Entry(models.Model):
    """
    An entrant submits an Entry to a Competition.
    """
    competition = models.ForeignKey(Competition)
    
    owner = models.ForeignKey(Profile)
    source_file = models.CharField(max_length=500)
    mp3_file = models.CharField(max_length=500)

    # length in seconds, grabbed from mp3_file metadata
    length = models.FloatField()

class EntryCommentThread(models.Model):
    """
    A thread, which contains comments about a particular position
    in the Entry.
    """

    entry = models.ForeignKey(Entry)

    # position in the song the comment was made.
    # negative number indicates no particular position
    position = models.FloatField()

class EntryComment(models.Model):
    """
    A comment in an EntryCommentThread
    """
    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(Profile)
    content = models.TextField()
    
class ThumbsUp(models.Model):
    """
    A ThumbsUp is something a user gives to a competition entry.
    """

    owner = models.ForeignKey(Profile)
    entry = models.ForeignKey(Entry)

    date_given = models.DateTimeField(auto_now=True)
