from django.test import TestCase
from django.test.client import Client
from django.core import mail

from opensourcemusic.main.models import *

from datetime import datetime, timedelta
import simplejson as json

class SimpleTest(TestCase):
    def setUp(self):
        # create the free account
        AccountPlan.objects.create(usd_per_month=0, total_space=1024*1024*1024*0.5, customer_id=0) 

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


    def test_register_account(self):
        # how many emails in outbox
        outboxCount = len(mail.outbox)
        # make sure the page loads
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        # register an account
        response = self.client.post('/register/', {
            'username': 'Rellik',
            'artist_name': 'Rellik',
            'email': 'rellik@mailinator.com',
            'password': 'temp1234',
            'confirm_password': 'temp1234',
        })
        self.assertRedirects(response, '/register/pending/')
        # verify the profile was created
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        # should not be activated
        self.assertEqual(profile.activated, False)

        # make sure email sent
        self.assertEqual(len(mail.outbox), outboxCount+1)

        # test register pending
        response = self.client.get('/register/pending/')
        self.assertEqual(response.status_code, 200)

        # test activate account
        # now fake the activation
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        response = self.client.get('/confirm/Rellik/%s/' % profile.activate_code)
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(profile.activated, True)

        # test register pending logged in
        self.client.login(username="Rellik", password="temp1234")
        response = self.client.get('/register/pending/')
        self.assertEqual(response.status_code, 200)

    def test_userpage(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/user/skiessi/')
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/user/skiessi/')
        self.assertEqual(response.status_code, 200)

    def test_ajax_login_state(self):
        # test logged in
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/ajax/login_state/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['is_authenticated'], True)
        self.assertEqual(data['user']['username'], "skiessi")

        # test logged out
        self.client.logout()
        response = self.client.get('/ajax/login_state/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['user']['is_authenticated'], False)

    def test_ajax_login(self):
        self.client.logout()
        response = self.client.post('/ajax/login/',
            {'username': "skiessi", 'password': 'temp1234'})
        self.assertEqual(response.status_code, 200)
        #TODO: assert logged in

    def test_ajax_logout(self):
        response = self.client.get('/ajax/logout/')
        self.assertEqual(response.status_code, 200)
        #TODO: assert logged out

    def test_login(self):
        self.client.logout()
        next_url = "/"
        response = self.client.post('/login/', {
            'username': "skiessi",
            'password': 'temp1234',
            'next_url': next_url
        })
        self.assertRedirects(response, next_url)
        #TODO: assert logged in
        
    def test_logout(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/logout/')
        #TODO: assert logged out

    def test_about(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_policy(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/policy/')
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/policy/')
        self.assertEqual(response.status_code, 200)

    def test_account(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 200)
