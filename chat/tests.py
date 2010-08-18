from chat import design
from chat.models import ChatRoom, ChatMessage, Appearance
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django_extensions.management.jobs import get_job
from main.tests import commonSetUp, commonTearDown
import main
import os
import simplejson as json
import subprocess

def system(command):
    "run a command on the system"
    p = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    return p.communicate()[0].strip()

def absolute(relative_path):
    "make a relative path absolute"
    return os.path.normpath(os.path.join(os.path.dirname(__file__), relative_path))

class SimpleTest(TestCase):
    def setUp(self):
        commonSetUp(self)
        register_url = reverse('register')

        # create some users
        for username in ("skiessi", "superjoe", "just64helpin"):
            self.client.post(register_url, {
                'username': username,
                'artist_name': username + ' band',
                'email': username + '@mailinator.com',
                'password': 'temp1234',
                'confirm_password': 'temp1234',
                'agree_to_terms': True,
                'plan': 0, 
            })
            code = User.objects.filter(username=username)[0].get_profile().activate_code
            self.client.get(reverse('confirm', args=(username, code)))

        self.skiessi = User.objects.filter(username="skiessi")[0]
        self.superjoe = User.objects.filter(username="superjoe")[0]
        self.just64helpin = User.objects.filter(username="just64helpin")[0]

        # create some chat rooms
        self.open_room = ChatRoom.objects.create(permission_type=ChatRoom.OPEN)
        self.open_room.save()
        self.white_room = ChatRoom.objects.create(permission_type=ChatRoom.WHITELIST)
        self.white_room.save()
        self.black_room = ChatRoom.objects.create(permission_type=ChatRoom.BLACKLIST)
        self.black_room.save()

        now = datetime.now()
        self.early_room = ChatRoom.objects.create(permission_type=ChatRoom.OPEN, start_date=now+timedelta(minutes=1), end_date=now+timedelta(minutes=2))
        self.late_room = ChatRoom.objects.create(permission_type=ChatRoom.OPEN, start_date=now-timedelta(minutes=2), end_date=now-timedelta(minutes=1))
        self.late_room = ChatRoom.objects.create(permission_type=ChatRoom.OPEN, start_date=now-timedelta(minutes=2), end_date=now-timedelta(minutes=1))

    def tearDown(self):
        commonTearDown(self)

    def test_hear(self):
        # create some messages for each room
        for room in (self.open_room, self.white_room, self.black_room):
            ChatMessage.objects.create(room=room, type=ChatMessage.MESSAGE, author=self.superjoe, message="hi from supajoe")
            ChatMessage.objects.create(room=room, type=ChatMessage.MESSAGE, author=self.skiessi, message="skuz saiz hai")
            ChatMessage.objects.create(room=room, type=ChatMessage.MESSAGE, author=self.just64helpin, message="jh")

        # anon requesting all messages, has permission
        self.client.logout()
        hear_url = reverse('chat.hear')
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], False)
        self.assertEqual(len(data['messages']), 3)

        # anon requesting all messages, no permission
        self.client.logout()
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.black_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], False)
        # can't talk but can still read messages
        self.assertEqual(len(data['messages']), 3)

        # requesting last 2 messages, has permission
        self.client.login(username="superjoe", password="temp1234")
        msg_id = ChatMessage.objects.filter(room=self.black_room,
            author=self.superjoe)[0].id
        response = self.client.get(hear_url, {
            'last_message': msg_id,
            'room': self.black_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], True)
        self.assertEqual(len(data['messages']), 2)

        # whitelist not authorized
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.white_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], False)
        self.assertEqual(data['user']['permission_write'], False)
        # private room, cannot read messages
        self.assertEqual(len(data['messages']), 0)

        # whitelist has permission
        self.white_room.whitelist.add(self.superjoe)
        self.white_room.save()
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.white_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], True)
        # first check, has 3 messages
        self.assertEqual(len(data['messages']), 3)

        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.white_room.id,
        })
        self.assertEqual(response.status_code, 200)
        # second check, has join message
        data = json.loads(response.content)
        self.assertEqual(len(data['messages']), 4)

        # blacklist has permission
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.black_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], True)
        # second peek of  black_room, contains join message
        self.assertEqual(len(data['messages']), 4)

        # blacklist not authorized
        self.black_room.blacklist.add(self.superjoe)
        self.black_room.save()
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.black_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], False)
        # can still read messages
        self.assertEqual(len(data['messages']), 4)

    def test_say(self):
        say_url = reverse('chat.say')
        # a room that is OK
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.post(say_url, {
            'room': self.open_room.id,
            'message': 'this is my message 1 2 3',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['user']['is_authenticated'], True)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], True)
        msg = ChatMessage.objects.filter(room=self.open_room, author=self.skiessi).order_by('-id')[0]
        self.assertEqual(msg.message, 'this is my message 1 2 3')

        # a message that is too long
        long_msg = 'x' * 5000
        response = self.client.post(say_url, {
            'room': self.open_room.id,
            'message': long_msg,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.message_too_long)

        # too early
        say_url = reverse('chat.say')
        response = self.client.post(say_url, {
            'room': self.early_room.id,
            'message': 'too early',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.room_is_not_active)
        self.assertEqual(ChatMessage.objects.count(), 1)

        # too late
        response = self.client.post(say_url, {
            'room': self.late_room.id,
            'message': 'too late',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.room_is_not_active)
        self.assertEqual(ChatMessage.objects.count(), 1)

        # not authenticated
        self.client.logout()
        response = self.client.post(say_url, {
            'room': self.open_room.id,
            'message': 'not authed',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], main.design.not_authenticated)
        self.assertEqual(ChatMessage.objects.count(), 1)

    def test_onliners(self):
        onliners_url = reverse('chat.onliners')
        hear_url = reverse('chat.hear')

        # anon, nobody there yet
        self.client.logout()
        response = self.client.get(onliners_url, {
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['data']), 0)

        # superjoe, see himself in the list
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.get(onliners_url, {
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['username'], 'superjoe')

        # pop skiessi online and anon check
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(onliners_url, {
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['data']), 2)

        # check an early one
        response = self.client.get(onliners_url, {
            'room': self.early_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['data']), 0)

    def test_leave_messages(self):
        hear_url = reverse('chat.hear')

        # make two appearances
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)

        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Appearance.objects.count(), 2)
        # pretend that superjoe's appearance was settings.CHAT_TIMEOUT + 1
        # seconds ago
        appear = Appearance.objects.filter(person=self.superjoe)[0]
        new_ts = datetime.now() - timedelta(seconds=(settings.CHAT_TIMEOUT+1))
        appear.timestamp = new_ts
        appear._save() # bypass the auto timestamp update
        appear = Appearance.objects.filter(person=self.superjoe)[0]
        self.assertEqual(appear.timestamp, new_ts)

        # run the job
        job = get_job('chat', 'leave')
        job().execute()

        # there should be a part message in the chat room
        response = self.client.get(hear_url, {
            'last_message': 'null',
            'room': self.open_room.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['permission_read'], True)
        self.assertEqual(data['user']['permission_write'], True)
        # 3 messages: join, join, leave
        self.assertEqual(len(data['messages']), 3)
        # have to sort locally
        data['messages'].sort(lambda x, y: cmp(x['id'], y['id']))
        self.assertEqual(data['messages'][2]['type'], ChatMessage.LEAVE)
        self.assertEqual(data['messages'][2]['author']['username'], 'superjoe')


        # now there should be 1 appearance
        self.assertEqual(Appearance.objects.count(), 1)
