from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.core.urlresolvers import reverse

from main.models import *
from chat.models import *
from competitions.models import *
from competitions.forms import *
from competitions import design
import settings

from datetime import datetime, timedelta
import simplejson as json

import os
import tempfile

def absolute(relative_path):
    "make a relative path absolute"
    return os.path.normpath(os.path.join(os.path.dirname(__file__), relative_path))

class SimpleTest(TestCase):
    def setUp(self):
        self.dirtyFiles = []

        # create the free account
        AccountPlan.objects.create(usd_per_month=0, total_space=1024*1024*1024*0.5, customer_id=0) 
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
            design.this_field_is_required)
        self.assertFormError(response, 'form', 'tz_offset',
            design.this_field_is_required)
        self.assertFormError(response, 'form', 'listening_party_date',
            design.lp_gt_submission_deadline)

        # submit the form, but don't give enough time until submission deadline
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
            'submission_deadline_date': self.validTimeStr(now + timedelta(minutes=1+settings.MINIMUM_COMPO_LENGTH-2)),
            'have_listening_party': 'on',
            #'party_immediately': False,
            'vote_time_quantity': 1,
            'vote_time_measurement': HOURS,
            'tz_offset': 0,
        })
        self.assertFormError(response, 'form', 'submission_deadline_date',
            design.give_at_least_x_minutes_to_work)
        self.assertFormError(response, 'form', 'listening_party_date',
            design.if_you_want_lp_set_date)

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
            design.cannot_start_compo_in_the_past)

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
        urlname_compo = 'arena.ajax_compo'

        # request a compo that doesn't exist
        response = self.client.get(reverse(urlname_compo, args=[4]))
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
        response = self.client.get(reverse(urlname_compo, args=[comp.id]))
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
        response = self.client.get(reverse(urlname_compo, args=[comp.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['compo']['theme'], "test theme 123")
        self.assertEqual(data['compo']['rules'], "test rules 123")

        ########## submitting entries ###############
        now = datetime.now()
        url_submit = reverse("arena.ajax_submit_entry")
        # try to submit to a bogus competition
        self.assertEqual(self.client.login(username='superjoe', password='temp1234'), True)
        mp3file = open(absolute('fixtures/silence10s-flstudio-notags.mp3'),'rb')
        response = self.client.post(url_submit, {
            'compo': 90, # bogus number
            'entry-file-mp3': mp3file,
            #'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        mp3file.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.competition_not_found)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)

        # try to submit to a not started competition
        comp.start_date = now + timedelta(minutes=1)
        comp.save()
        mp3file = open(absolute('fixtures/silence10s-flstudio-notags.mp3'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.competition_not_started)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)

        # try to submit after the deadline
        comp.start_date = now - timedelta(minutes=1)
        comp.submit_deadline = now - timedelta(minutes=1)
        comp.save()
        mp3file = open(absolute('fixtures/silence10s-flstudio-notags.mp3'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.past_submission_deadline)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)

        # try to submit logged out
        comp.start_date = now - timedelta(minutes=1)
        comp.submit_deadline = now + timedelta(minutes=1)
        comp.save()
        self.client.logout()
        mp3file = open(absolute('fixtures/silence10s-flstudio-notags.mp3'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)

        # try to submit without providing mp3 file
        self.assertEqual(self.client.login(username='superjoe', password='temp1234'), True)
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            #'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.mp3_required)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)

        # submit a file that is too big
        # create a temp file that is > settings.FILE_UPLOAD_SIZE_CAP
        handle = tempfile.NamedTemporaryFile(suffix='mp3', delete=False)
        self.dirtyFiles.append(handle.name)
        bytesWritten = 0
        bufferSize = 1024 * 1024
        while bytesWritten <= settings.FILE_UPLOAD_SIZE_CAP:
            handle.write(" " * bufferSize)
            bytesWritten += bufferSize
        handle.close()
        mp3file = open(handle.name,'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.mp3_too_big)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)
        os.remove(handle.name)

        # submit an mp3 file that is too long 
        mp3file = open(absolute('fixtures/silence11m-notags.mp3'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.song_too_long)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)

        # submit an ogg file instead of mp3
        mp3file = open(absolute('fixtures/silence10s-flstudio-notags.ogg'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "test title 123",
            'entry-comments': "test comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'] in (design.sketchy_mp3_file,
            design.invalid_mp3_file), True)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Song.objects.count(), 0)

        # submit a good file, don't provide source or comments
        # flstudio exported, no tags
        self.assertEqual(self.client.login(username='superjoe', password='temp1234'), True)
        mp3file = open(absolute('fixtures/silence10s-flstudio-notags.mp3'),'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            #'entry-file-source': sourcefile,
            'entry-title': "superjoe title 123",
            #'entry-comments': "test comments 123",
        })
        mp3file.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Song.objects.count(), 1)
        entry = Entry.objects.filter(owner=self.superjoe)[0]
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.mp3_file)), True)
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.waveform_img)), True)
        self.assertEqual(entry.song.band.id, self.superjoe.get_profile().solo_band.id)
        self.assertEqual(entry.song.title, 'superjoe title 123')

        # submit a good file, provide source and commentts
        # flstudio exported, tags
        self.assertEqual(self.client.login(username='just64helpin', password='temp1234'), True)
        mp3file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "just64helpin title 123",
            'entry-comments': "just64helpin comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(Entry.objects.count(), 2)
        self.assertEqual(Song.objects.count(), 2)
        entry = Entry.objects.filter(owner=self.just64helpin)[0]
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.mp3_file)), True)
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.waveform_img)), True)
        self.assertEqual(entry.song.band.id, self.just64helpin.get_profile().solo_band.id)
        self.assertEqual(entry.song.title, 'just64helpin title 123')
        self.assertEqual(entry.song.comments, 'just64helpin comments 123')

        # submit a good file, provide source but no comments
        # no tags, vbr
        self.assertEqual(self.client.login(username='skiessi', password='temp1234'), True)
        mp3file = open(absolute('fixtures/silence10s-notags-vbr.mp3'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "skiessi title 123",
            #'entry-comments': "skiessi comments 123",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(Entry.objects.count(), 3)
        self.assertEqual(Song.objects.count(), 3)
        entry = Entry.objects.filter(owner=self.skiessi)[0]
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.mp3_file)), True)
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.waveform_img)), True)
        self.assertEqual(entry.song.band.id, self.skiessi.get_profile().solo_band.id)
        self.assertEqual(entry.song.title, 'skiessi title 123')

        # resubmit
        mp3file = open(absolute('fixtures/silence10s-notags-vbr.mp3'),'rb')
        sourcefile = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(url_submit, {
            'compo': comp.id,
            'entry-file-mp3': mp3file,
            'entry-file-source': sourcefile,
            'entry-title': "skiessi title 123 v2",
            'entry-comments': "skiessi comments 123 v2",
        })
        mp3file.close()
        sourcefile.close()
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(Entry.objects.count(), 3)
        self.assertEqual(Song.objects.count(), 3)
        entry = Entry.objects.filter(owner=self.skiessi)[0]
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.mp3_file)), True)
        self.assertEqual(os.path.exists(os.path.join(settings.MEDIA_ROOT, entry.song.waveform_img)), True)
        self.assertEqual(entry.song.band.id, self.skiessi.get_profile().solo_band.id)
        self.assertEqual(entry.song.title, 'skiessi title 123 v2')
        self.assertEqual(entry.song.comments, 'skiessi comments 123 v2')

        # check ajax_compo to make sure it gets the entry list right
        response = self.client.get(reverse(urlname_compo, args=[comp.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['is_authenticated'], True)
        self.assertEqual(len(data['entries']), 3)
        self.assertEqual(data['entries'][0]['owner']['username'], 'superjoe')
        self.assertEqual(data['entries'][1]['owner']['username'],'just64helpin')
        self.assertEqual(data['entries'][2]['owner']['username'], 'skiessi')

        ############# voting ################
        urlname_vote = 'arena.ajax_vote'
        urlname_unvote = 'arena.ajax_unvote'
        comp.have_listening_party = False
        comp.submit_deadline = now - timedelta(minutes=1)
        comp.vote_deadline = now + timedelta(minutes=1)
        comp.save()

        ############ voting ###############
        # try to vote logged out
        self.client.logout()
        response = self.client.get(reverse(urlname_vote, args=[entry.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)
        self.assertEqual(ThumbsUp.objects.count(), 0)

        # 2 people vote for superjoe, make sure he has 2 votes
        # skiessi vote for superjoe
        self.assertEqual(self.client.login(username='skiessi', password='temp1234'), True)
        entry = Entry.objects.filter(owner=self.superjoe)[0]
        response = self.client.get(reverse(urlname_vote, args=[entry.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(ThumbsUp.objects.filter(entry=entry).count(), 1)

        # just64helpin vote for superjoe
        self.assertEqual(self.client.login(username='just64helpin', password='temp1234'), True)
        response = self.client.get(reverse(urlname_vote, args=[entry.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(ThumbsUp.objects.filter(entry=entry).count(), 2)

        # make sure his vote count is decremented
        response = self.client.get(reverse(urlname_compo, args=[comp.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['votes']['max'], 1)
        self.assertEqual(len(data['votes']['used']), 1)
        self.assertEqual(data['votes']['used'][0]['entry'], entry.id)
        self.assertEqual(data['votes']['left'], 0)
        
        # vote for yourself (invalid)
        self.assertEqual(self.client.login(username='superjoe', password='temp1234'), True)
        response = self.client.get(reverse(urlname_vote, args=[entry.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.cannot_vote_for_yourself)
        self.assertEqual(ThumbsUp.objects.filter(entry=entry).count(), 2)

        # skiessi unvote
        self.assertEqual(self.client.login(username='skiessi', password='temp1234'), True)
        entry = Entry.objects.filter(owner=self.superjoe)[0]
        response = self.client.get(reverse(urlname_unvote, args=[entry.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(ThumbsUp.objects.filter(entry=entry).count(), 1)

        # make sure his vote count is correct
        response = self.client.get(reverse(urlname_compo, args=[comp.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['votes']['max'], 1)
        self.assertEqual(len(data['votes']['used']), 0)
        self.assertEqual(data['votes']['left'], 1)

        # try unvoting logged out
        self.client.logout()
        response = self.client.get(reverse(urlname_unvote, args=[entry.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)

        # close the competition and then look at ajax_compo
        # make sure person with most votes is first
        comp.vote_deadline = now - timedelta(minutes=1)
        comp.save()
        self.assertEqual(comp.isClosed(), True)
        response = self.client.get(reverse(urlname_compo, args=[comp.id]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['entries']), 3)
        self.assertEqual(data['entries'][0]['owner']['id'], self.superjoe.id)
        self.assertEqual(data['entries'][0]['vote_count'], 1)

    def rm(self, filename):
        if os.path.exists(filename):
            os.remove(filename)

    def tearDown(self):
        "undo changes to the file system"
        for dirt in self.dirtyFiles:
            self.rm(dirt)
        self.dirtyFiles = []

        for song in Song.objects.all():
            if song.mp3_file:
                self.rm(os.path.join(settings.MEDIA_ROOT, song.mp3_file))
            if song.source_file:
                self.rm(os.path.join(settings.MEDIA_ROOT, song.source_file))
            if song.waveform_img:
                self.rm(os.path.join(settings.MEDIA_ROOT, song.waveform_img))
