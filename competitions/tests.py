from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.core.urlresolvers import reverse

from opensourcemusic.main.models import *
from opensourcemusic.competitions.models import *
from opensourcemusic.chat.models import *

from opensourcemusic.competitions.forms import *

from opensourcemusic import settings

from datetime import datetime, timedelta
import simplejson as json

class SimpleTest(TestCase):
    def setUp(self):
        # create some users
        register_url = reverse("register")
        for username in ("skiessi", "superjoe", "just64helpin"):
            response = self.client.post(register_url, {
                'username': username,
                'artist_name': username + ' band',
                'email': username + '@mailinator.com',
                'password': 'temp1234',
                'confirm_password': 'temp1234',
            })
            code = User.objects.filter(username=username)[0].get_profile().activate_code
            confirm_url = reverse("confirm", args=(username, code))
            response = self.client.get(confirm_url)
            self.assertEqual(response.status_code, 200)

        self.skiessi = User.objects.filter(username="skiessi")[0]
        self.superjoe = User.objects.filter(username="superjoe")[0]
        self.just64helpin = User.objects.filter(username="just64helpin")[0]

    def test_home(self):
        url = reverse('arena.home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_ajax_available(self):
        """
        tests available, owned, bookmark, and unbookmark
        """
        url = reverse('arena.ajax_available')
        # should be no competitions available
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 0)

        # make a competition
        now = datetime.now()
        comp = Competition()
        comp.title = "test compo 123"
        comp.host = self.skiessi
        comp.theme = "test theme 123"
        comp.preview_theme = False
        comp.rules = "test rules 123"
        comp.preview_rules = True
        comp.start_date = now + timedelta(minutes=1)
        comp.submit_deadline = now + timedelta(minutes=2)
        comp.listening_party_start_date = comp.submit_deadline
        comp.listening_party_end_date = comp.listening_party_start_date
        comp.vote_period_length = 60 # seconds
        comp.chat_room = ChatRoom.objects.create()
        comp.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 1)
        self.assertEqual(data['compos'][0]['title'], 'test compo 123')
        # compo can't have theme yet because it didn't start yet
        self.assertEqual(data['compos'][0].has_key('theme'), False)
        # rules are on preview though
        self.assertEqual(data['compos'][0]['rules'], 'test rules 123')

        # log in and bookmark the competition
        self.assertEqual(self.client.login(username="superjoe", password="temp1234"), True)
        bookmark_url = reverse("arena.ajax_bookmark", args=[comp.id])
        response = self.client.get(bookmark_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 0)

        # unbookmark it
        unbookmark_url = reverse("arena.ajax_unbookmark", args=[comp.id])
        response = self.client.get(unbookmark_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 1)

        # delete it
        comp.delete()
        
        # make sure paging works
        howMany = settings.ITEMS_PER_PAGE * 3 # should be 3 pages
        for i in range(howMany):
            now = datetime.now()
            comp = Competition()
            comp.title = "title"
            comp.host = self.superjoe
            comp.theme = "theme"
            comp.preview_theme = True
            comp.rules = "rules"
            comp.preview_rules = True
            comp.start_date = now - timedelta(minutes=1)
            comp.submit_deadline = now + timedelta(minutes=1)
            comp.listening_party_start_date = comp.submit_deadline
            comp.listening_party_end_date = comp.listening_party_start_date
            comp.vote_period_length = 60 # seconds
            comp.chat_room = ChatRoom.objects.create()
            comp.save()

        # default first page
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), settings.ITEMS_PER_PAGE)
        self.assertEqual(data['compos'][0]['theme'], 'theme')
        self.assertEqual(data['compos'][0]['rules'], 'rules')
        self.assertEqual(data['compos'][0]['title'], 'title')
        self.assertEqual(data['page_count'], 3)
        self.assertEqual(data['page_number'], 1)

        # get second page
        response = self.client.get(url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), settings.ITEMS_PER_PAGE)
        self.assertEqual(data['page_count'], 3)
        self.assertEqual(data['page_number'], 2)

    def test_ajax_owned(self):
        url = reverse('arena.ajax_owned')
        # should be not authenticated
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['is_authenticated'], False)

        # should be no competitions available
        self.assertEqual(self.client.login(username="skiessi", password="temp1234"), True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 0)

        # make a competition
        now = datetime.now()
        comp = Competition()
        comp.title = "test compo 123"
        comp.host = self.skiessi
        comp.theme = "test theme 123"
        comp.preview_theme = False
        comp.rules = "test rules 123"
        comp.preview_rules = True
        comp.start_date = now + timedelta(minutes=1)
        comp.submit_deadline = now + timedelta(minutes=2)
        comp.listening_party_start_date = comp.submit_deadline
        comp.listening_party_end_date = comp.listening_party_start_date
        comp.vote_period_length = 60 # seconds
        comp.chat_room = ChatRoom.objects.create()
        comp.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 0)

        # log in and bookmark the competition
        bookmark_url = reverse("arena.ajax_bookmark", args=[comp.id])
        response = self.client.get(bookmark_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 1)
        self.assertEqual(data['compos'][0]['title'], 'test compo 123')
        # compo can't have theme yet because it didn't start yet
        self.assertEqual(data['compos'][0].has_key('theme'), False)
        # rules are on preview though
        self.assertEqual(data['compos'][0]['rules'], 'test rules 123')

        # unbookmark it
        unbookmark_url = reverse("arena.ajax_unbookmark", args=[comp.id])
        response = self.client.get(unbookmark_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['compos']), 0)

    def test_ajax_bookmark(self):
        """
        this is tested by available and owned above, not necessary.
        """
        pass

    def test_ajax_unbookmark(self):
        """
        again, tested by available and owned above, not necessary.
        """
        pass

    def test_competition(self):
        """
        tests the html page for competition.
        """
        urlname = "arena.compete"
        # make a competition
        now = datetime.now()
        comp = Competition()
        comp.title = "test compo 123"
        comp.host = self.skiessi
        comp.theme = "test theme 123"
        comp.preview_theme = False
        comp.rules = "test rules 123"
        comp.preview_rules = False
        comp.start_date = now + timedelta(minutes=1)
        comp.submit_deadline = now + timedelta(minutes=2)
        comp.listening_party_start_date = comp.submit_deadline
        comp.listening_party_end_date = comp.listening_party_start_date
        comp.vote_period_length = 60 # seconds
        comp.chat_room = ChatRoom.objects.create()
        comp.save()

        # compo doesn't exist (404)
        response = self.client.get(reverse(urlname, args=[9])) # bogus index
        self.assertEqual(response.status_code, 404)

        # logged out
        self.client.logout()
        response = self.client.get(reverse(urlname, args=[comp.id])) 
        self.assertEqual(response.status_code, 200)

        # logged in
        self.assertEqual(self.client.login(username="superjoe", password="temp1234"), True)
        response = self.client.get(reverse(urlname, args=[comp.id])) 
        self.assertEqual(response.status_code, 200)

    def validTimeStr(self, dt):
        "returns a good string representing the datetime specified"
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def test_create(self):
        "test creating a competition"
        url = reverse("arena.create")
        url_login = reverse("user_login")

        # load the page, not logged in
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # load the page, logged in
        self.assertEqual(self.client.login(username="superjoe", password="temp1234"), True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # submit the form, leave stuff blank
        # also set a listening party before the submit deadline
        now = datetime.now()
        response = self.client.post(url, {
            'have_theme': 'on',
            #'preview_theme': False,
            'theme': "test theme 123",
            'have_rules': 'on',
            'preview_rules': 'on',
            'rules': "test rules 123",
            'start_date': self.validTimeStr(now + timedelta(minutes=1)),
            'submission_deadline_date': self.validTimeStr(now + timedelta(hours=1)),
            'have_listening_party': 'on',
            #'party_immediately': False,
            'listening_party_date': self.validTimeStr(now + timedelta(minutes=2)),
            'vote_time_quantity': 1,
            'vote_time_measurement': HOURS,
        })
        self.assertFormError(response, 'form', 'title',
            "This field is required.")
        self.assertFormError(response, 'form', 'tz_offset',
            "This field is required.")
        self.assertFormError(response, 'form', 'listening_party_date',
            "Listening party must be after submission deadline.")

        # submit the form, but only give 1 minute until submission deadline
        # also say we want a listening party but don't give a date
        response = self.client.post(url, {
            'title': "test compo 123",
            'have_theme': 'on',
            #'preview_theme': False,
            'theme': "test theme 123",
            'have_rules': 'on',
            'preview_rules': 'on',
            'rules': "test rules 123",
            'start_date': self.validTimeStr(now + timedelta(minutes=1)),
            'submission_deadline_date': self.validTimeStr(now + timedelta(minutes=2)),
            'have_listening_party': 'on',
            #'party_immediately': False,
            'vote_time_quantity': 1,
            'vote_time_measurement': HOURS,
            'tz_offset': 0,
        })
        self.assertFormError(response, 'form', 'submission_deadline_date',
            "You have to give people at least 10 minutes to work.")
        self.assertFormError(response, 'form', 'listening_party_date',
            "If you want a listening party, you need to set a date.")

        # submit the form, but give a compo start date in the past
        response = self.client.post(url, {
            'title': "test compo 123",
            'have_theme': 'on',
            #'preview_theme': False,
            'theme': "test theme 123",
            'have_rules': 'on',
            'preview_rules': 'on',
            'rules': "test rules 123",
            'start_date': self.validTimeStr(now - timedelta(minutes=1)),
            'submission_deadline_date': self.validTimeStr(now + timedelta(hours=1)),
            'have_listening_party': 'on',
            'party_immediately': 'on',
            #'listening_party_date': None,
            'vote_time_quantity': 1,
            'vote_time_measurement': HOURS,
            'tz_offset': 0,
        })
        self.assertFormError(response, 'form', 'start_date',
            "You cannot start a competition in the past.")

        # so far there shouldn't be any competition objects
        self.assertEqual(Competition.objects.count(), 0)

        # submit a valid compo
        response = self.client.post(url, {
            'title': "test compo 123",
            'have_theme': True,
            #'preview_theme': False,
            'theme': "test theme 123",
            'have_rules': True,
            'preview_rules': True,
            'rules': "test rules 123",
            'start_date': self.validTimeStr(now + timedelta(minutes=1)),
            'submission_deadline_date': self.validTimeStr(now + timedelta(hours=1)),
            'have_listening_party': True,
            'party_immediately': True,
            #'listening_party_date': None,
            'vote_time_quantity': 1,
            'vote_time_measurement': HOURS,
            'tz_offset': 0,
        })
        url_arena = reverse("arena.home")
        self.assertRedirects(response, url_arena)

        # now there should be one competition
        self.assertEqual(Competition.objects.count(), 1)
        comp = Competition.objects.all()[0]
        self.assertEqual(comp.title, "test compo 123")
        self.assertEqual(comp.theme, "test theme 123")
        self.assertEqual(comp.rules, "test rules 123")
        self.assertEqual(comp.isClosed(), False)

        # there should also be a chatroom created for it
        self.assertEqual(ChatRoom.objects.count(), 1)
        self.assertEqual(ChatRoom.objects.all()[0].is_active(), True)

    def test_ajax_competition(self):
        """
        this tests:
            ajax_compo 
            ajax_vote
            ajax_unvote
            ajax_submit_entry
        """
        urlname = 'arena.ajax_compo'

        # request a compo that doesn't exist
        response = self.client.get(reverse(urlname, args=[4]))
        self.assertEqual(response.status_code, 404)

        # create a competition that hasn't started yet
        now = datetime.now()
        comp = Competition()
        comp.title = "test compo 123"
        comp.host = self.skiessi
        comp.theme = "test theme 123"
        comp.preview_theme = False
        comp.rules = "test rules 123"
        comp.preview_rules = False
        comp.start_date = now + timedelta(minutes=1)
        comp.submit_deadline = now + timedelta(minutes=2)
        comp.listening_party_start_date = comp.submit_deadline
        comp.listening_party_end_date = comp.listening_party_start_date
        comp.vote_period_length = 60 # seconds
        comp.chat_room = ChatRoom.objects.create()
        comp.save()

        # check that the request works
        response = self.client.get(reverse(urlname, args=[comp.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['is_authenticated'], False)
        self.assertEqual(data.has_key('votes'), False)
        self.assertEqual(data['compo'].has_key('theme'), False)
        self.assertEqual(data['compo'].has_key('rules'), False)
        self.assertEqual(data['compo']['title'], "test compo 123")
        self.assertEqual(data['party']['buffer_time'],
            settings.LISTENING_PARTY_BUFFER_TIME)

        # adjust the date so that it is started
        comp.start_date = now - timedelta(minutes=1)
        comp.save()
        
        # make sure we can see the rules and theme now
        response = self.client.get(reverse(urlname, args=[comp.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['compo']['theme'], "test theme 123")
        self.assertEqual(data['compo']['rules'], "test rules 123")

        # submit an entry
        



#    url('^ajax/compo/(\d+)/$', 'opensourcemusic.competitions.views.ajax_compo', name="arena.ajax_compo"),
#    url('^ajax/vote/(\d+)/$', 'opensourcemusic.competitions.views.ajax_vote', name="arena.ajax_vote"),
#    url('^ajax/unvote/(\d+)/$', 'opensourcemusic.competitions.views.ajax_unvote', name="arena.ajax_unvote"),
#    url('^ajax/submit-entry/$', 'opensourcemusic.competitions.views.ajax_submit_entry', name="arena.ajax_submit_entry"),
#

#)
    def tearDown(self):
        "undo changes to the file system"
        pass
