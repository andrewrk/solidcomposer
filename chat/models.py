from django.db import models
from django.contrib.auth.models import User

from datetime import datetime

from base.models import SerializableModel

SYSTEM, ACTION, MESSAGE, JOIN, LEAVE, NOTICE = range(6)
OPEN, WHITELIST, BLACKLIST = range(3)

class ChatRoom(SerializableModel):
    """
    ChatRoom contains ChatMessages and manages who is allowed to be in it
    """
    PERMISSION_TYPES = (
        (OPEN, 'open'),
        (WHITELIST, 'whitelist'),
        (BLACKLIST, 'blacklist'),
    )
    OWNER_ATTRS = (
        'whitelist',
        'blacklist',
    )
    PUBLIC_ATTRS = (
        'start_date',
        'end_date',
        'permission_type',
    )

    permission_type = models.IntegerField(choices=PERMISSION_TYPES, default=OPEN)
    whitelist = models.ManyToManyField(User, null=True, blank=True, related_name="whitelisted_users")
    blacklist = models.ManyToManyField(User, null=True, blank=True, related_name="blacklisted_users")

    # the date that chat becomes active. null means no bound
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def permission_to_hear(self, user):
        "whether a user has permission to read messages in this channel"
        if self.permission_type in (OPEN, BLACKLIST):
            return True
        else:
            # user has to be signed in and on the whitelist
            return user.is_authenticated() and self.whitelist.filter(pk=user.id).count() == 1

    def permission_to_chat(self, user):
        "whether a user has permission to talk in this channel"
        # user has to be signed in
        if not user.is_authenticated():
            return False

        if self.permission_type == OPEN:
            return True
        else:
            if self.permission_type == WHITELIST:
                # user has to be on the whitelist
                if self.whitelist.filter(pk=user.id).count() != 1:
                    return False
            elif self.permission_type == BLACKLIST:
                # user is blocked if he is on the blacklist 
                if self.blacklist.filter(pk=user.id).count() == 1:
                    return False

            return True

    def is_active(self):
        """
        returns True if and only if the current date and time is
        within the chat room's active period.
        """
        now = datetime.now()
        if not self.start_date is None:
            if self.start_date > now:
                return False
        if not self.end_date is None:
            if self.end_date < now:
                return False
        return True


    def __unicode__(self):
        return "ChatRoom %i" % self.id

class ChatMessage(SerializableModel):
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

    PUBLIC_ATTRS = (
        'room',
        'type',
        'author',
        'message',
        'timestamp',
    )

    room = models.ForeignKey('ChatRoom')
    type = models.IntegerField(choices=MESSAGE_TYPES)
    author = models.ForeignKey(User, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        "Update populated fields before saving"
        self.timestamp = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        "Save without any auto field population"
        super(ChatMessage, self).save(*args, **kwargs)

    def __unicode__(self):
        """
        Each message type has a special representation, return
        that representation.
        """
        if self.type == SYSTEM:
            return u'SYSTEM: %s' % self.message[:30]
        elif self.type == JOIN:
            return 'JOIN: %s' % self.author
        elif self.type == LEAVE:
            return 'LEAVE: %s' % self.author
        elif self.type == ACTION:
            return 'ACTION: %s > %s' % (self.author, self.message[:30])
        return self.message[:30]

class Appearance(SerializableModel):
    """
    An Appearance tracks when a person was seen in a ChatRoom.
    """
    PUBLIC_ATTRS = (
        'person',
        'room',
        'timestamp',
    )

    person = models.ForeignKey(User)
    room = models.ForeignKey('ChatRoom')
    timestamp = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        self.timestamp = datetime.now()
        self._save(*args, **kwargs)

    def _save(self, *args, **kwargs):
        super(Appearance, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s in %s on %s" % (self.person, self.room, self.timestamp)
