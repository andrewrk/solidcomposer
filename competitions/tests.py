from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.core.urlresolvers import reverse

from opensourcemusic.main.models import *
from opensourcemusic.competitions.models import *
from opensourcemusic.chat.models import *

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
        self.client.login(username="superjoe", password="temp1234")
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
        self.client.login(username="skiessi", password="temp1234")
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

#    url('^ajax/compo/(\d+)/$', 'opensourcemusic.competitions.views.ajax_compo', name="arena.ajax_compo"),
#    url('^ajax/vote/(\d+)/$', 'opensourcemusic.competitions.views.ajax_vote', name="arena.ajax_vote"),
#    url('^ajax/unvote/(\d+)/$', 'opensourcemusic.competitions.views.ajax_unvote', name="arena.ajax_unvote"),
#    url('^ajax/submit-entry/$', 'opensourcemusic.competitions.views.ajax_submit_entry', name="arena.ajax_submit_entry"),
#
#    url('^create/$', 'opensourcemusic.competitions.views.create', name="arena.create"),
#    url('^compete/(\d+)/$', 'opensourcemusic.competitions.views.competition', name="arena.compete"),
#)
    def tearDown(self):
        "undo changes to the file system"
        pass
