from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from main.models import Song, TempFile, SongCommentNode, BandMember, Band, \
    Profile
from main import design
from main.common import superwalk
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
        outbox_count = len(mail.outbox) #@UndefinedVariable
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
        self.assertEqual(len(mail.outbox), outbox_count+1) #@UndefinedVariable

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

    def test_dashbard(self):
        url = reverse('dashboard')
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(url)
        self.assertRedirects(response, reverse("user_login") + "?next=" + url)

    def test_landing(self):
        return self.staticPage(reverse('landing'))

    def test_account_plan(self):
        account_plan = reverse('account.plan')

        # give skiessi an upgraded account
        skiessi_profile = self.skiessi.get_profile()
        skiessi_profile.purchased_bytes = 1000
        skiessi_profile.save()
        skiessi_solo = skiessi_profile.solo_band
        skiessi_member = BandMember.objects.get(band=skiessi_solo, user=self.skiessi)

        # skiessi create another band
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(reverse('workbench.create_band'), {
            'band_name': 'Monkey Band',
        })
        self.assertEqual(response.status_code, 302)
        monkey_band = Band.objects.order_by('-pk')[0]
        monkey_member = BandMember.objects.order_by('-pk')[0]

        log_entry_count = LogEntry.objects.count()

        # anon
        self.client.logout()
        response = self.client.post(account_plan, {
            'member-{0}-amt'.format(skiessi_member.id): 2000,
        })
        self.assertRedirects(response, reverse('user_login') + "?next=" + account_plan)
        self.assertEqual(log_entry_count, LogEntry.objects.count())

        # change band donation amount
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(account_plan, {
            'member-{0}-amt'.format(skiessi_member.id): 500,
            'member-{0}-amt'.format(monkey_member.id): 250,
        })
        self.assertRedirects(response, account_plan)
        monkey_band = Band.objects.get(pk=monkey_band.id)
        monkey_member = BandMember.objects.get(pk=monkey_member.id)
        skiessi_solo = Band.objects.get(pk=skiessi_solo.id)
        skiessi_member = BandMember.objects.get(pk=skiessi_member.id)
        self.assertEqual(monkey_band.total_space, settings.BAND_INIT_SPACE + 250)
        self.assertEqual(skiessi_solo.total_space, settings.BAND_INIT_SPACE + 500)
        self.assertEqual(self.skiessi.get_profile().space_used(), 750)
        self.assertEqual(self.skiessi.get_profile().purchased_bytes, 1000)
        # verify that log entry was created
        log_entry_count += 2
        self.assertEqual(log_entry_count, LogEntry.objects.count())
        log_entry = LogEntry.objects.get(band=skiessi_solo)
        self.assertEqual(log_entry.entry_type, LogEntry.SPACE_ALLOCATED_CHANGE)
        self.assertEqual(log_entry.catalyst, self.skiessi)
        self.assertEqual(log_entry.old_amount, 0)
        self.assertEqual(log_entry.new_amount, 500)
        log_entry = LogEntry.objects.get(band=monkey_band)
        self.assertEqual(log_entry.entry_type, LogEntry.SPACE_ALLOCATED_CHANGE)
        self.assertEqual(log_entry.catalyst, self.skiessi)
        self.assertEqual(log_entry.old_amount, 0)
        self.assertEqual(log_entry.new_amount, 250)

        # try to give more bytes to a band than we can
        response = self.client.post(account_plan, {
            'member-{0}-amt'.format(skiessi_member.id): 1001,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err_msg'], design.you_dont_have_enough_space_to_do_that)
        self.assertEqual(log_entry_count, LogEntry.objects.count())
        monkey_band = Band.objects.get(pk=monkey_band.id)
        monkey_member = BandMember.objects.get(pk=monkey_member.id)
        skiessi_solo = Band.objects.get(pk=skiessi_solo.id)
        skiessi_member = BandMember.objects.get(pk=skiessi_member.id)
        self.assertEqual(monkey_band.total_space, settings.BAND_INIT_SPACE + 250)
        self.assertEqual(skiessi_solo.total_space, settings.BAND_INIT_SPACE + 500)
        self.assertEqual(self.skiessi.get_profile().space_used(), 750)

        # try to give bytes to a band that we're not a member of
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(account_plan, {
            'member-{0}-amt'.format(skiessi_member.id): 500,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err_msg'], design.can_only_edit_your_own_amount_donated)

    def test_account_plan_changed(self):
        # url(r'^account/plan/changed/$', 'main.views.changed_plan_results', {'SSL': True}, name="account.plan_changed"),
        pass
    
    def test_signup_pending(self):
        # url(r'^signup/pending/$', 'main.views.register_pending', {'SSL': True}, name="register_pending"),
        pass

    def test_account_email(self):
        # url(r'^account/email/$', 'main.views.account_email', {'SSL': True}, name="account.email"),
        account_email_url = reverse('account.email')
        profile = self.just64helpin.get_profile()

        # anon
        self.client.logout()
        response = self.client.get(account_email_url)
        self.assertRedirects(response, reverse('user_login') + "?next=" + account_email_url)
        
        # getting the page, logged in
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.get(account_email_url)
        self.assertEqual(response.status_code, 200)

        # turn off getting email
        response = self.client.post(account_email_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success'], True)
        profile = Profile.objects.get(pk=profile.id)
        self.assertEqual(profile.email_notifications, False)
        self.assertEqual(profile.email_newsletter, False)

        # turn on getting email
        response = self.client.post(account_email_url, {
            'notifications': 'On',
            'newsletter': 'On',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['success'], True)
        profile = Profile.objects.get(pk=profile.id)
        self.assertEqual(profile.email_notifications, True)
        self.assertEqual(profile.email_newsletter, True)

    def test_account_password(self):
        # url(r'^account/password/$', 'main.views.account_password', {'SSL': True}, name="account.password"),
        account_password = reverse('account.password')

        # TODO: test failure conditions
        
        # change just64helpin's password to boobies
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(account_password, {
            'old_password': 'temp1234',
            'new_password': 'boobies',
            'confirm_password': 'boobies',
        })
        self.assertEqual(response.status_code, 200)
        self.just64helpin = User.objects.get(pk=self.just64helpin.id)
        self.client.logout()
        self.client.login(username='just64helpin', password='boobies')

    def test_account_password_reset(self):
        # url(r'^account/password/reset/$', 'main.views.account_password_reset', {'SSL': True}, name="account.password.reset"),
        account_password_reset = reverse('account.password.reset')

        outbox_count = len(mail.outbox)
        self.assertEqual(outbox_count, len(mail.outbox))

        # TODO: test failure conditions
        
        self.client.logout()
        self.staticPage(account_password_reset)

        # reset skiessi's password
        response = self.client.post(account_password_reset, {
            'email': self.skiessi.email,
        })
        self.assertEqual(response.status_code, 200)
        outbox_count += 1
        self.assertEqual(outbox_count, len(mail.outbox))
    
    def test_plans(self):
        return self.staticPage(reverse('plans'))

    def test_article(self):
        # url(r'^article/([\w\d-]+)/$', 'main.views.article', name='article'),
        article_url = lambda article: reverse('article', args=[article])

        # should return 404 if template not found
        response = self.client.get(article_url('bogus-article-does-not-exist-12349919929hqcrxdarcot'))
        self.assertEqual(response.status_code, 404)

        # should return a static page if found
        # test all static pages
        def lsdir(folder):
            for dirpath, _dirnames, filenames in os.walk(folder):
                for filename in filenames:
                    yield os.path.join(dirpath, filename)
                break
        for filename in lsdir(os.path.join(os.path.dirname(__file__), '..', 'templates', 'articles')):
            path, title = os.path.split(filename)
            url, ext = os.path.splitext(title)
            self.staticPage(article_url(url))
        
    def test_home(self):
        self.staticPage('/') # make sure we have a home page.
        self.staticPage(reverse('home'))
