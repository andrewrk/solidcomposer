from main.models import *
from workshop.models import *

from django.test import TestCase
from django.test.client import Client
from django.core import mail
from django.core.urlresolvers import reverse

from datetime import datetime, timedelta
import simplejson as json

from django.conf import settings

import os

def rm(filename):
    if os.path.exists(filename):
        os.remove(filename)

def commonSetUp(obj):
    # use test bucket
    obj.prev_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    settings.AWS_STORAGE_BUCKET_NAME = settings.AWS_TEST_STORAGE_BUCKET_NAME

def commonTearDown(obj):
    # restore original bucket
    settings.AWS_STORAGE_BUCKET_NAME = obj.prev_bucket_name

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

class SimpleTest(TestCase):
    def setUp(self):
        # use test bucket
        self.prev_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        settings.AWS_STORAGE_BUCKET_NAME = settings.AWS_TEST_STORAGE_BUCKET_NAME

        register_url = reverse('register')

        # create some users
        for username in ("skiessi", "superjoe", "just64helpin"):
            response = self.client.post(register_url, {
                'username': username,
                'artist_name': username + ' band',
                'email': username + '@mailinator.com',
                'password': 'temp1234',
                'confirm_password': 'temp1234',
                'agree_to_terms': True
            })
            code = User.objects.filter(username=username)[0].get_profile().activate_code
            response = self.client.get(reverse('confirm', args=(username, code)))

        self.skiessi = User.objects.filter(username="skiessi")[0]
        self.superjoe = User.objects.filter(username="superjoe")[0]
        self.just64helpin = User.objects.filter(username="just64helpin")[0]

    def tearDown(self):
        settings.AWS_STORAGE_BUCKET_NAME = self.prev_bucket_name

    def test_register_account(self):
        register_url = reverse('register')
        register_pending_url = reverse('register_pending')

        # how many emails in outbox
        outboxCount = len(mail.outbox)
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
        })
        self.assertRedirects(response, register_pending_url)
        # verify the profile was created
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        # should not be activated
        self.assertEqual(profile.activated, False)

        # make sure email sent
        self.assertEqual(len(mail.outbox), outboxCount+1)

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
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(reverse('userpage', args=['skiessi']))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('userpage', args=['skiessi']))
        self.assertEqual(response.status_code, 200)

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
        #TODO: assert logged out

    def test_about(self):
        about_url = reverse('about')
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(about_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(about_url)
        self.assertEqual(response.status_code, 200)

    def test_policy(self):
        policy_url = reverse('policy')
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(policy_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(policy_url)
        self.assertEqual(response.status_code, 200)

    def test_account(self):
        account_url = reverse('account')
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(account_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(account_url)
        self.assertEqual(response.status_code, 200)

    def test_terms(self):
        terms_url = reverse('terms')
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get(terms_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(terms_url)
        self.assertEqual(response.status_code, 200)
