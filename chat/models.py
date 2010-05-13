from django.db import models
from django.contrib.auth.models import User

SYSTEM, ACTION, MESSAGE, JOIN, LEAVE, NOTICE = range(6)
OPEN, WHITELIST, BLACKLIST = range(3)

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
    whitelist = models.ManyToManyField(User, null=True, blank=True, related_name="whitelisted_users")
    blacklist = models.ManyToManyField(User, null=True, blank=True, related_name="blacklisted_users")

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
    author = models.ForeignKey(User, blank=True, null=True)
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
    person = models.ForeignKey(User)
    room = models.ForeignKey('ChatRoom')
    timestamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s in %s on %s" % (self.person, self.room, self.timestamp)
