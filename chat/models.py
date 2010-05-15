from django.db import models
from django.contrib.auth.models import User

SYSTEM, ACTION, MESSAGE, JOIN, LEAVE, NOTICE = range(6)
OPEN, WHITELIST, BLACKLIST = range(3)

class ChatRoom(models.Model):
    """
    ChatRoom contains ChatMessages and manages who is allowed to be in it

    # create a test user
    >>> bob = User.objects.create_user('bob', 'bob@bob.bob', 'bob1')
    >>> bob.save()

    >>> anon = django.contrib.auth.models.AnonymousUser()
    >>> anon.is_authenticated()
    False

    # create some test rooms
    >>> now = datetime.now()
    >>> open_room = ChatRoom.objects.create(permission_type=OPEN)
    >>> white_room = ChatRoom.objects.create(permission_type=WHITELIST)
    >>> white_room.save()
    >>> black_room = ChatRoom.objects.create(permission_type=BLACKLIST)
    >>> black_room.save()

    # test permission to chat
    >>> open_room.permission_to_chat(anon)
    True
    >>> white_room.permission_to_chat(anon)
    False
    >>> black_room.permission_to_chat(anon)
    False
    >>> open_room.permission_to_chat(bob)
    True
    >>> white_room.permission_to_chat(bob)
    False
    >>> white_room.whitelist.add(bob)
    >>> white_room.permission_to_chat(bob)
    True
    >>> black_room.permission_to_chat(bob)
    True
    >>> black_room.blacklist.add(bob)
    >>> black_room.permission_to_chat(bob)
    False
    >>> True
    False
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

    permission_type = models.IntegerField(choices=PERMISSION_TYPES, default=OPEN)
    whitelist = models.ManyToManyField(User, null=True, blank=True, related_name="whitelisted_users")
    blacklist = models.ManyToManyField(User, null=True, blank=True, related_name="blacklisted_users")

    # the date that chat becomes active. null means no bound
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def permission_to_chat(self, user):
        """
        returns True if user has access to this room.
        """
        if self.permission_type == OPEN:
            return True
        else:
            # user has to be signed in
            if not user.is_authenticated():
                return False

            if self.permission_type == WHITELIST:
                # user has to be on the whitelist
                if self.whitelist.filter(pk=user.id).count() != 1:
                    return False
            elif self.permission_type == BLACKLIST:
                # user is blocked if he is on the blacklist 
                if self.blacklist.filter(pk=user.id).count() == 1:
                    return False

            return True


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
