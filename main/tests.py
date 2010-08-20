from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from main.models import Song, TempFile, SongCommentNode
from main import design
from workshop.models import SampleFile, LogEntry
import os
import simplejson as json
from datetime import datetime, timedelta

def rm(filename):
    if os.path.exists(filename):
        os.remove(filename)

def commonSetUp(obj):
    # use test bucket
    obj.prev_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    settings.AWS_STORAGE_BUCKET_NAME = settings.AWS_TEST_STORAGE_BUCKET_NAME
    settings.TESTING = True

def commonTearDown(obj):
    # restore original bucket
    settings.AWS_STORAGE_BUCKET_NAME = obj.prev_bucket_name
    settings.TESTING = False

    import storage

    for song in Song.objects.all():
        if song.mp3_file:
            storage.engine.delete(song.mp3_file)
        if song.source_file:
            storage.engine.delete(song.source_file)
        if song.waveform_img:
            storage.engine.delete(song.waveform_img)

    for sample in SampleFile.objects.all():
        storage.engine.delete(sample.path)

    for tmp in TempFile.objects.all():
        rm(tmp.path)

def absolute(relative_path):
    "make a relative path absolute"
    return os.path.normpath(os.path.join(os.path.dirname(__file__), relative_path))

class SimpleTest(TestCase):
    def setUp(self):
        commonSetUp(self)

        register_url = reverse('register')

        # create some users
        for username in ("skiessi", "superjoe", "just64helpin"):
            response = self.client.post(register_url, {
                'username': username,
                'artist_name': username + ' band',
                'email': username + '@mailinator.com',
                'password': 'temp1234',
                'confirm_password': 'temp1234',
                'agree_to_terms': True,
                'plan': 0,
            })
            self.assertEqual(response.status_code, 302)
            code = User.objects.get(username=username).get_profile().activate_code
            self.client.get(reverse('confirm', args=(username, code)))

        self.skiessi = User.objects.get(username="skiessi")
        self.superjoe = User.objects.get(username="superjoe")
        self.just64helpin = User.objects.get(username="just64helpin")

    def tearDown(self):
        commonTearDown(self)

    def staticPage(self, url):
        "tests if the page doesn't error out logged in and logged out."
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_register_account(self):
        register_url = reverse('register')
        register_pending_url = reverse('register_pending')

        # how many emails in outbox
        outboxCount = len(mail.outbox) #@UndefinedVariable
        # make sure the page loads
        response = self.client.get(register_url)
        self.assertEqual(response.status_code, 200)

        # register an account but don't check agree_to_terms
        response = self.client.post(register_url, {
            'username': 'Rellik',
            'artist_name': 'Rellik',
            'email': 'rellik@mailinator.com',
            'password': 'temp1234',
            'confirm_password': 'temp1234',
        })
        self.assertEqual(response.status_code, 200)
        # verify the profile was not created
        self.assertEqual(User.objects.filter(username='Rellik').count(), 0)

        # register an account
        response = self.client.post(register_url, {
            'username': 'Rellik',
            'artist_name': 'Rellik',
            'email': 'rellik@mailinator.com',
            'password': 'temp1234',
            'confirm_password': 'temp1234',
            'agree_to_terms': True,
            'plan': 0,
        })
        self.assertRedirects(response, register_pending_url)
        # verify the profile was created
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        # should not be activated
        self.assertEqual(profile.activated, False)

        # make sure email sent
        self.assertEqual(len(mail.outbox), outboxCount+1) #@UndefinedVariable

        # test register pending
        response = self.client.get(register_pending_url)
        self.assertEqual(response.status_code, 200)

        # test activate account
        # now fake the activation
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        response = self.client.get(reverse('confirm', args=['Rellik', profile.activate_code]))
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(profile.activated, True)

        # test register pending logged in
        self.client.login(username="Rellik", password="temp1234")
        response = self.client.get(register_pending_url)
        self.assertEqual(response.status_code, 200)

    def test_userpage(self):
        self.staticPage(reverse('userpage', args=['superjoe']))
        self.staticPage(reverse('userpage', args=['skiessi']))

    def test_ajax_login_state(self):
        ajax_login_state_url = reverse('ajax_login_state')
        # test logged in
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(ajax_login_state_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['is_authenticated'], True)
        self.assertEqual(data['user']['username'], "skiessi")

        # test logged out
        self.client.logout()
        response = self.client.get(ajax_login_state_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['is_authenticated'], False)

    def test_ajax_login(self):
        ajax_login_url = reverse('ajax_login')

        self.client.logout()
        response = self.client.post(ajax_login_url,
            {'username': "skiessi", 'password': 'temp1234'})
        self.assertEqual(response.status_code, 200)
        #TODO: assert logged in

    def test_ajax_logout(self):
        ajax_logout_url = reverse('ajax_logout')
        response = self.client.get(ajax_logout_url)
        self.assertEqual(response.status_code, 200)
        #TODO: assert logged out

    def test_login(self):
        login_url = reverse('user_login')

        self.client.logout()
        next_url = "/"
        response = self.client.post(login_url, {
            'username': "skiessi",
            'password': 'temp1234',
            'next_url': next_url
        })
        self.assertRedirects(response, next_url)
        #TODO: assert logged in
        
    def test_logout(self):
        logout_url = reverse('user_logout')
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(logout_url)
        self.assertEqual(response.status_code, 302)
        #TODO: assert logged out

    def test_policy(self):
        return self.staticPage(reverse('policy'))

    def test_terms(self):
        return self.staticPage(reverse('terms'))

    def test_comment(self):
        ajax_comment = reverse('ajax_comment')
        log_entry_count = LogEntry.objects.count()

        # create a song to comment on
        superjoe_solo = self.superjoe.get_profile().solo_band
        blank_mp3file = open(absolute('../workshop/fixtures/silence10s-flstudio-tags.mp3'),'rb')
        blank_project = open(absolute('../workshop/fixtures/blank.flp'),'rb')
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(reverse('workbench.create_project', args=[superjoe_solo.id]), {
            'title': "Blank",
            'file_source': blank_project,
            'file_mp3': blank_mp3file,
            'comments': "parent comments",
        })
        self.assertEqual(response.status_code, 302)
        parent_node = SongCommentNode.objects.order_by('-pk')[0]
        comment_count = SongCommentNode.objects.count()
        log_entry_count += 1
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # anon
        self.client.logout()
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': 'first',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # bogus parent
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_comment, {
            'parent': 1231,
            'content': 'first',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_song_comment_node_id)
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # does not have permission to critique
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': 'first',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_comment)
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # parent has reply disabled
        parent_node.reply_disabled = True
        parent_node.save()
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': 'first',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.comments_disabled_for_this_version)
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # no content
        parent_node.reply_disabled = False
        parent_node.save()
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': '',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.content_wrong_length)
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # content too long
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': 'a' * 2001,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.content_wrong_length)
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # position longer than song
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': 'first',
            'position': 15,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.invalid_position)
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # ok, no position
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': 'first',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['data']['song'], parent_node.song.id)
        self.assertEqual(data['data']['parent'], parent_node.id)
        self.assertEqual(data['data']['content'], 'first')
        node = SongCommentNode.objects.order_by('-pk')[0]
        self.assertEqual(node.song, parent_node.song)
        self.assertEqual(node.parent, parent_node)
        self.assertEqual(node.content, 'first')
        comment_count += 1
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        comment = SongCommentNode.objects.order_by('-pk')[0]
        self.assertEqual(comment.song, parent_node.song)
        self.assertEqual(comment.parent, parent_node)
        self.assertEqual(comment.content, 'first')
        log_entry_count += 1
        self.assertEqual(log_entry_count, LogEntry.objects.count())
        log_entry = LogEntry.objects.order_by('-pk')[0]
        self.assertEqual(log_entry.entry_type, LogEntry.SONG_CRITIQUE)
        self.assertEqual(log_entry.band, superjoe_solo)
        self.assertEqual(log_entry.catalyst, self.superjoe)
        self.assertEqual(log_entry.node, comment)

        # ok, with position
        response = self.client.post(ajax_comment, {
            'parent': parent_node.id,
            'content': 'second',
            'position': 7,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['data']['song'], parent_node.song.id)
        self.assertEqual(data['data']['parent'], parent_node.id)
        self.assertEqual(data['data']['content'], 'second')
        node = SongCommentNode.objects.order_by('-pk')[0]
        self.assertEqual(node.song, parent_node.song)
        self.assertEqual(node.parent, parent_node)
        self.assertEqual(node.content, 'second')
        comment_count += 1
        self.assertEqual(comment_count, SongCommentNode.objects.count())
        comment = SongCommentNode.objects.order_by('-pk')[0]
        self.assertEqual(comment.song, parent_node.song)
        self.assertEqual(comment.parent, parent_node)
        self.assertEqual(comment.content, 'second')
        log_entry_count += 1
        self.assertEqual(log_entry_count, LogEntry.objects.count())
        log_entry = LogEntry.objects.order_by('-pk')[0]
        self.assertEqual(log_entry.entry_type, LogEntry.SONG_CRITIQUE)
        self.assertEqual(log_entry.band, superjoe_solo)
        self.assertEqual(log_entry.catalyst, self.superjoe)
        self.assertEqual(log_entry.node, comment)

    def test_delete_comment(self):
        ajax_delete_comment = reverse('ajax_delete_comment')

        # create a song to comment on
        superjoe_solo = self.superjoe.get_profile().solo_band
        blank_mp3file = open(absolute('../workshop/fixtures/silence10s-flstudio-tags.mp3'),'rb')
        blank_project = open(absolute('../workshop/fixtures/blank.flp'),'rb')
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(reverse('workbench.create_project', args=[superjoe_solo.id]), {
            'title': "Blank",
            'file_source': blank_project,
            'file_mp3': blank_mp3file,
            'comments': "parent comments",
        })
        self.assertEqual(response.status_code, 302)
        parent_node = SongCommentNode.objects.order_by('-pk')[0]

        # create a comment on that song to test
        response = self.client.post(reverse('ajax_comment'), {
            'parent': parent_node.id,
            'content': 'first',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        comment_count = SongCommentNode.objects.count()
        target_comment = SongCommentNode.objects.order_by('-pk')[0]

        # anon
        self.client.logout()
        response = self.client.post(ajax_delete_comment, {
            'comment': target_comment.id,
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)
        self.assertEqual(comment_count, SongCommentNode.objects.count())

        # bogus comment id
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_delete_comment, {
            'comment': 928,
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_song_comment_node_id)
        self.assertEqual(comment_count, SongCommentNode.objects.count())

        # someone else's comment
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(ajax_delete_comment, {
            'comment': target_comment.id,
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.can_only_delete_your_own_comment)
        self.assertEqual(comment_count, SongCommentNode.objects.count())

        # try to delete after a day has gone by
        target_comment.date_created = datetime.now() - timedelta(days=1, hours=1)
        target_comment.save()
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_delete_comment, {
            'comment': target_comment.id,
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.too_late_to_delete_comment)
        self.assertEqual(comment_count, SongCommentNode.objects.count())

        # delete a leaf node. it should actually get deleted.
        target_comment.date_created = datetime.now()
        target_comment.save()
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_delete_comment, {
            'comment': target_comment.id,
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        comment_count -= 1
        self.assertEqual(comment_count, SongCommentNode.objects.count())

        # try to delete the root comment node for a song
        response = self.client.post(ajax_delete_comment, {
            'comment': parent_node.id,
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        parent_node = SongCommentNode.objects.get(pk=parent_node.id)
        self.assertEqual(parent_node.content, '')

        # delete a comment that has a leaf attached to it. should only set deleted to True.
        # TODO

    def test_edit_comment(self):
        ajax_edit_comment = reverse('ajax_edit_comment')

        # create a song to comment on
        superjoe_solo = self.superjoe.get_profile().solo_band
        blank_mp3file = open(absolute('../workshop/fixtures/silence10s-flstudio-tags.mp3'),'rb')
        blank_project = open(absolute('../workshop/fixtures/blank.flp'),'rb')
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(reverse('workbench.create_project', args=[superjoe_solo.id]), {
            'title': "Blank",
            'file_source': blank_project,
            'file_mp3': blank_mp3file,
            'comments': "parent comments",
        })
        self.assertEqual(response.status_code, 302)
        parent_node = SongCommentNode.objects.order_by('-pk')[0]

        # create a comment on that song to test
        response = self.client.post(reverse('ajax_comment'), {
            'parent': parent_node.id,
            'content': 'original',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        target_comment = SongCommentNode.objects.order_by('-pk')[0]

        # anon
        self.client.logout()
        response = self.client.post(ajax_edit_comment, {
            'comment': target_comment.id,
            'content': 'new',
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)
        target_comment = SongCommentNode.objects.get(pk=target_comment.id)
        self.assertEqual(target_comment.content, 'original')

        # bogus comment id
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_edit_comment, {
            'comment': 232,
            'content': 'new',
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_song_comment_node_id)
        target_comment = SongCommentNode.objects.get(pk=target_comment.id)
        self.assertEqual(target_comment.content, 'original')

        # try to edit someone else's comment
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(ajax_edit_comment, {
            'comment': target_comment.id,
            'content': 'new',
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.can_only_edit_your_own_comment)
        target_comment = SongCommentNode.objects.get(pk=target_comment.id)
        self.assertEqual(target_comment.content, 'original')

        # try to edit after a day has gone by
        target_comment.date_created = datetime.now() - timedelta(days=1, minutes=1)
        target_comment.save()
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_edit_comment, {
            'comment': target_comment.id,
            'content': 'new',
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.too_late_to_edit_comment)
        target_comment = SongCommentNode.objects.get(pk=target_comment.id)
        self.assertEqual(target_comment.content, 'original')

        # no content
        target_comment.date_created = datetime.now()
        target_comment.save()
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_edit_comment, {
            'comment': target_comment.id,
            'content': '',
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.content_wrong_length)
        target_comment = SongCommentNode.objects.get(pk=target_comment.id)
        self.assertEqual(target_comment.content, 'original')

        # content too long
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_edit_comment, {
            'comment': target_comment.id,
            'content': 'a' * 2001,
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.content_wrong_length)
        target_comment = SongCommentNode.objects.get(pk=target_comment.id)
        self.assertEqual(target_comment.content, 'original')

        # ok
        response = self.client.post(ajax_edit_comment, {
            'comment': target_comment.id,
            'content': 'new',
        })
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        target_comment = SongCommentNode.objects.get(pk=target_comment.id)
        self.assertEqual(target_comment.content, 'new')

