from django.db import models
from django.contrib.auth.models import User
from base.models import SerializableModel

from datetime import datetime, timedelta

class Competition(SerializableModel):
    PUBLIC_ATTRS = (
        'title',
        'preview_theme',
        'preview_rules',
        'start_date',
        'submit_deadline',
        'have_listening_party',
        'listening_party_start_date',
        'listening_party_end_date',
        'vote_deadline',
        'vote_period_length',
        'chat_room',
        'host',
    )
    OWNER_ATTRS = (
        'theme',
        'rules',
    )

    title = models.CharField(max_length=256)

    # who created the competition
    host = models.ForeignKey(User)

    # optional
    theme = models.TextField(blank=True)
    # can entrants view the theme before it starts?
    preview_theme = models.BooleanField(default=False)

    # optional
    rules = models.TextField(blank=True)
    # can entrants view the rules before it starts?
    preview_rules = models.BooleanField(default=True)

    # when this competition was created
    date_created = models.DateTimeField()

    # when the theme is announced / when the competition starts
    start_date = models.DateTimeField()

    # deadline for submitting entries
    submit_deadline = models.DateTimeField()

    have_listening_party = models.BooleanField(default=False)
    # must be after submit_deadline, with enough time for
    # processing.
    listening_party_start_date = models.DateTimeField(blank=True, null=True)

    # set this date to listening_party_start_date. it will be updated when
    # someone submits an entry
    listening_party_end_date = models.DateTimeField(blank=True, null=True)

    # deadline for casting votes. must be after listening party end time,
    # which is undetermined. People must have at least 10 minutes to vote,
    # so when the processing from the submit_deadline is finished, it will
    # recalculate this value based on the then-known listening_party_end_date
    vote_deadline = models.DateTimeField(blank=True, null=True)

    # length of the voting period in seconds. Used to calculate vote_deadline
    # after listening party end date is computed.
    vote_period_length = models.BigIntegerField()

    # one chat room per competition
    chat_room = models.ForeignKey('chat.ChatRoom', blank=True, null=True)

    def themeVisible(self):
        return self.preview_theme or datetime.now() >= self.start_date

    def rulesVisible(self):
        return self.preview_rules or datetime.now() >= self.start_date

    def isClosed(self):
        "Returns True if and only if the competition is closed."
        now = datetime.now()
        return self.vote_deadline is not None and now >= self.vote_deadline

    def __unicode__(self):
        return "%s on %s" % (self.title, self.start_date)

    def save(self, *args, **kwargs):
        "Update populated fields before saving"
        if not self.id:
            self.date_created = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        "Save without any auto field population"
        super(Competition, self).save(*args, **kwargs)

    def to_dict(self, access=SerializableModel.PUBLIC, chains=[]):
        data = super(Competition, self).to_dict(access, chains)
        if self.themeVisible():
            data['theme'] = self.theme
        if self.rulesVisible():
            data['rules'] = self.rules
        return data

    def changeListeningPartyStartDate(self, date):
        """
        Use this method to change the lp start date. It automatically updates
        listening_party_end_date, vote_deadline, and have_listening_party
        Use date=None to mean no listening party.
        """
        vote_period_delta = timedelta(seconds=self.vote_period_length)
        if date is None:
            self.have_listening_party = False
            self.vote_deadline = self.submit_deadline + vote_period_delta
            self.listening_party_start_date = date
        else:
            self.have_listening_party = True
            lp_length = self.listening_party_end_date - self.listening_party_start_date
            self.vote_deadline = self.listening_party_end_date + vote_period_delta
            self.listening_party_start_date = date
            self.listening_party_end_date = date + lp_length

class ThumbsUp(SerializableModel):
    """
    A ThumbsUp is something a user gives to a competition entry.
    """
    PUBLIC_ATTRS = (
        'owner',
        'entry',
    )

    owner = models.ForeignKey(User)
    entry = models.ForeignKey('Entry')
    date_given = models.DateTimeField()

    def __unicode__(self):
        return "%s gives +1 to %s" % (self.owner, self.entry)

    def save(self, *args, **kwargs):
        "Update populated fields before saving"
        self.date_given = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        "Save without any auto field population"
        super(ThumbsUp, self).save(*args, **kwargs)

class Entry(SerializableModel):
    """
    An entrant submits an Entry to a Competition.
    """
    PUBLIC_ATTRS = (
        'competition',
        'owner',
        'song',
        'submit_date',
        'edit_date',
    )

    competition = models.ForeignKey(Competition)
    owner = models.ForeignKey(User)
    song = models.ForeignKey('main.Song')
    submit_date = models.DateTimeField()
    edit_date = models.DateTimeField()

    def __unicode__(self):
        return "%s in %s" % (self.song, self.competition)

    def save(self, *args, **kwargs):
        self.edit_date = datetime.now()
        if not self.id:
            self.submit_date = self.edit_date
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(Entry, self).save(*args, **kwargs)

    def to_dict(self, access=SerializableModel.PUBLIC, chains=[]):
        data = super(Entry, self).to_dict(access, chains)
        if self.competition.isClosed():
            data['vote_count'] = ThumbsUp.objects.filter(entry=self).count()
        return data
