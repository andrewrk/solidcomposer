from django.test import TestCase
from django.test.client import Client
from django.core import mail

from opensourcemusic.main.models import *

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


    def test_register_account(self):
        # how many emails in outbox
        outboxCount = len(mail.outbox)
        # make sure the page loads
        response = self.client.get('/register/')
        self.failUnlessEqual(response.status_code, 200)
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
        self.failUnlessEqual(profile.activated, False)

        # make sure email sent
        self.assertEquals(len(mail.outbox), outboxCount+1)

        # test register pending
        response = self.client.get('/register/pending/')
        self.failUnlessEqual(response.status_code, 200)

        # test activate account
        # now fake the activation
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        response = self.client.get('/confirm/Rellik/%s/' % profile.activate_code)
        profile = User.objects.filter(username='Rellik')[0].get_profile()
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(profile.activated, True)

        # test register pending logged in
        self.client.login(username="Rellik", password="temp1234")
        response = self.client.get('/register/pending/')
        self.failUnlessEqual(response.status_code, 200)

    def test_userpage(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/user/skiessi/')
        self.failUnlessEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/user/skiessi/')
        self.failUnlessEqual(response.status_code, 200)

    def test_ajax_login_state(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/ajax/login_state/')
        self.failUnlessEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/ajax/login_state/')
        self.failUnlessEqual(response.status_code, 200)

    def test_ajax_login(self):
        self.client.logout()
        response = self.client.post('/ajax/login/',
            {'username': "skiessi", 'password': 'temp1234'})
        self.failUnlessEqual(response.status_code, 200)
        #TODO: assert logged in

    def test_ajax_logout(self):
        response = self.client.get('/ajax/logout/')
        self.failUnlessEqual(response.status_code, 200)
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
        self.failUnlessEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/about/')
        self.failUnlessEqual(response.status_code, 200)

    def test_policy(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/policy/')
        self.failUnlessEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/policy/')
        self.failUnlessEqual(response.status_code, 200)

    def test_account(self):
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.get('/account/')
        self.failUnlessEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get('/account/')
        self.failUnlessEqual(response.status_code, 200)
