from django.test import TestCase
from django.test.client import Client
from django.core import mail

from opensourcemusic.main.models import *
from opensourcemusic.chat.models import *

from datetime import datetime, timedelta
import simplejson as json

class SimpleTest(TestCase):
    def setUp(self):
        # create some users
        for username in ("skiessi", "superjoe", "just64helpin"):
            response = self.client.post('/register/', {
                'username': username,
                'artist_name': username + ' band',
                'email': username + '@mailinator.com',
                'password': 'temp1234',
                'confirm_password': 'temp1234',
            })
            code = User.objects.filter(username=username)[0].get_profile().activate_code
            response = self.client.get('/confirm/%s/%s/' % (username, code))

        self.skiessi = User.objects.filter(username="skiessi")[0]
        self.superjoe = User.objects.filter(username="superjoe")[0]
        self.just64helpin = User.objects.filter(username="just64helpin")[0]

        # create some chat rooms
        self.open_room = ChatRoom.objects.create(permission_type=OPEN)
        self.white_room = ChatRoom.objects.create(permission_type=WHITELIST)
        self.white_room.save()
        self.black_room = ChatRoom.objects.create(permission_type=BLACKLIST)
        self.black_room.save()

        now = datetime.now()
        self.early_room = ChatRoom.objects.create(permission_type=OPEN, start_date=now+timedelta(minutes=1), end_date=now+timedelta(minutes=2))
        self.late_room = ChatRoom.objects.create(permission_type=OPEN, start_date=now-timedelta(minutes=2), end_date=now-timedelta(minutes=1))
        self.late_room = ChatRoom.objects.create(permission_type=OPEN, start_date=now-timedelta(minutes=2), end_date=now-timedelta(minutes=1))

    def test_hear(self):
        # create some messages for each room
        for room in (self.open_room, self.white_room, self.black_room):
            ChatMessage.objects.create(room=room, type=MESSAGE, author=self.superjoe, message="hi from supajoe")
            ChatMessage.objects.create(room=room, type=MESSAGE, author=self.skiessi, message="skuz saiz hai")
            ChatMessage.objects.create(room=room, type=MESSAGE, author=self.just64helpin, message="jh")

        # anon requesting all messages, has permission
        self.client.logout()
        response = self.client.get('/chat/ajax/hear/', {
            'last_message': 'null',
            'room': self.open_room.id,
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['has_permission'], True)
        self.assertEquals(len(data['messages']), 3)

        # anon requesting all messages, no permission
        self.client.logout()
        response = self.client.get('/chat/ajax/hear/', {
            'last_message': 'null',
            'room': self.black_room.id,
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['has_permission'], False)

        # requesting last 2 messages, has permission
        self.client.login(username="superjoe", password="temp1234")
        msg_id = ChatMessage.objects.filter(room=self.black_room,
            author=self.superjoe)[0].id
        response = self.client.get('/chat/ajax/hear/', {
            'last_message': msg_id,
            'room': self.black_room.id,
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['has_permission'], True)
        self.assertEquals(len(data['messages']), 2)

        # whitelist not authorized
        response = self.client.get('/chat/ajax/hear/', {
            'last_message': 'null',
            'room': self.white_room.id,
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['has_permission'], False)

        # whitelist has permission
        self.white_room.whitelist.add(self.superjoe)
        self.white_room.save()
        response = self.client.get('/chat/ajax/hear/', {
            'last_message': 'null',
            'room': self.white_room.id,
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['has_permission'], True)
        # second check of whitelist, has join message
        self.assertEquals(len(data['messages']), 4)

        # blacklist has permission
        response = self.client.get('/chat/ajax/hear/', {
            'last_message': 'null',
            'room': self.black_room.id,
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['has_permission'], True)
        # second peek of  black_room, contains join message
        self.assertEquals(len(data['messages']), 4)

        # blacklist not authorized
        self.black_room.blacklist.add(self.superjoe)
        self.black_room.save()
        response = self.client.get('/chat/ajax/hear/', {
            'last_message': 'null',
            'room': self.black_room.id,
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['has_permission'], False)

    def test_say(self):
        # a room that is OK
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.post('/chat/ajax/say/', {
            'room': self.open_room.id,
            'message': 'this is my message 1 2 3',
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['is_authenticated'], True)
        self.assertEquals(data['user']['has_permission'], True)
        self.assertEquals(data['success'], True)
        msg = ChatMessage.objects.filter(room=self.open_room, author=self.skiessi).order_by('-id')[0]
        self.assertEquals(msg.message, 'this is my message 1 2 3')

        # too early
        response = self.client.post('/chat/ajax/say/', {
            'room': self.early_room.id,
            'message': 'too early',
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['is_authenticated'], True)
        self.assertEquals(data['success'], False)

        # too late
        response = self.client.post('/chat/ajax/say/', {
            'room': self.late_room.id,
            'message': 'too late',
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['is_authenticated'], True)
        self.assertEquals(data['success'], False)

        # not authenticated
        self.client.logout()
        response = self.client.post('/chat/ajax/say/', {
            'room': self.open_room.id,
            'message': 'not authed',
        })
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data['user']['is_authenticated'], False)
        self.assertEquals(data['success'], False)

   # (r'^ajax/online/$', 'opensourcemusic.chat.views.ajax_onliners'),
