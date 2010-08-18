from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from main.models import BandMember, Band, Profile, Song
from main.tests import commonSetUp, commonTearDown
from django.contrib.auth.models import User

from workshop.models import BandInvitation, Project, ProjectVersion, \
    PluginDepenency, Studio, SampleDependency, UploadedSample, SampleFile
from workshop import syncdaw
from workshop import design

import simplejson as json
from datetime import datetime, timedelta

from main.common import create_hash, file_hash

import os, hashlib

def absolute(relative_path):
    "make a relative path absolute"
    return os.path.normpath(os.path.join(os.path.dirname(__file__), relative_path))

class SimpleTest(TestCase):
    def verifyAjax(self, response):
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)

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
            code = User.objects.get(username=username).get_profile().activate_code
            self.client.get(reverse('confirm', args=(username, code)))

        self.skiessi = User.objects.get(username="skiessi")
        self.superjoe = User.objects.get(username="superjoe")
        self.just64helpin = User.objects.get(username="just64helpin")

        syncdaw.logging = False
        syncdaw.syncdaw()

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

    def anonPostFail(self, url, data):
        self.client.logout()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)
        return response

    def anonGetFail(self, url, data):
        self.client.logout()
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)
        return response

    def checkLoginRedirect(self, url):
        self.client.logout()
        response = self.client.get(url)
        login_url = reverse('user_login') + "?next=" + url
        self.assertRedirects(response, login_url)

    def setUpTBA(self):
        """
        creates a band called The Burning Awesome with superjoe and skiessi excluding just64helpin.
        superjoe is manager and skiessi is band member.
        creates two projects: 
            The Castle - Only one ProjectVersion.
            Top Hat - Only one ProjectVersion.
        """
        # superjoe create The Burning Awesome
        self.client.login(username='superjoe', password='temp1234')
        self.verifyAjax(self.client.post(reverse('workbench.ajax_create_band'), {
            'band_name': 'The Burning Awesome',
        }))
        tba = Band.objects.get(title='The Burning Awesome')
        # superjoe invite skiessi
        self.verifyAjax(self.client.post(reverse('workbench.ajax_create_invite'), {
            'band': tba.id,
            'invitee': self.skiessi.id,
        }))
        invite = BandInvitation.objects.order_by('-pk')[0]
        # skiessi accept invite
        self.client.login(username='skiessi', password='temp1234')
        self.verifyAjax(self.client.post(reverse('workbench.ajax_accept_invite'), {
            'invitation': invite.id,
        }))
        # skiessi create The Castle 
        blank_mp3file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'),'rb')
        blank_project = open(absolute('fixtures/4frontpiano.flp'),'rb')
        response = self.client.post(reverse('workbench.create_project', args=[tba.id]), {
            'title': "The Castle",
            'file_source': blank_project,
            'file_mp3': blank_mp3file,
            'comments': "The Castle Comments",
        })
        self.assertEqual(response.status_code, 302)
        # superjoe create Top Hat
        self.client.login(username='superjoe', password='temp1234')
        blank_mp3file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'),'rb')
        blank_project = open(absolute('fixtures/blank.flp'),'rb')
        response = self.client.post(reverse('workbench.create_project', args=[tba.id]), {
            'title': "Top Hat",
            'file_source': blank_project,
            'file_mp3': blank_mp3file,
            'comments': "Top Hat Comments",
        })
        self.assertEqual(response.status_code, 302)

    def test_home(self):
        return self.staticPage(reverse('workbench.home'))
        
    def test_create_invite(self):
        ajax_create_invite = reverse("workbench.ajax_create_invite")
        ajax_accept_invite = reverse("workbench.ajax_accept_invite")
        self.assertEqual(BandInvitation.objects.count(), 0)
        outbox_count = len(mail.outbox)

        # anonymous, inviting just64helpin to superjoe's band
        superjoe_solo = self.superjoe.get_profile().solo_band
        self.anonPostFail(ajax_create_invite, {
            'band': superjoe_solo.id,
            'invitee': self.just64helpin.id,
        })
        self.assertEqual(len(mail.outbox), outbox_count)
        
        # skiessi logged in, inviting just64helpin to superjoe's band
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(ajax_create_invite, {
            'band': superjoe_solo.id,
            'invitee': self.just64helpin.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.can_only_invite_to_your_own_band)
        self.assertEqual(len(mail.outbox), outbox_count)

        # skiessi logged in, inviting just64helpin to skiessi's band (should actually work)
        skiessi_solo = self.skiessi.get_profile().solo_band
        response = self.client.post(ajax_create_invite, {
            'band': skiessi_solo.id,
            'invitee': self.just64helpin.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        invite = BandInvitation.objects.all()[0]
        self.assertEqual(invite.inviter, self.skiessi)
        self.assertEqual(invite.band, skiessi_solo)
        self.assertEqual(invite.role, BandMember.BAND_MEMBER)
        self.assertEqual(invite.invitee, self.just64helpin)
        outbox_count += 1
        self.assertEqual(len(mail.outbox), outbox_count)
        
        # same thing (already invited, so should not work)
        response = self.client.post(ajax_create_invite, {
            'band': skiessi_solo.id,
            'invitee': self.just64helpin.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.already_invited_x_to_your_band.format(self.just64helpin.username))
        self.assertEqual(len(mail.outbox), outbox_count)

        # test if just64helpin is already in the band
        self.client.logout()
        self.client.login(username="just64helpin", password="temp1234")
        response = self.client.post(ajax_accept_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        outbox_count += 1
        self.assertEqual(len(mail.outbox), outbox_count)

        self.client.logout()
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.post(ajax_create_invite, {
            'band': skiessi_solo.id,
            'invitee': self.just64helpin.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.x_already_in_band.format(self.just64helpin.username))
        self.assertEqual(len(mail.outbox), outbox_count)

        # just64helpin try to invite but he's not a manager
        # TODO

    def test_ignore_invite(self):
        ajax_ignore_invite = reverse('workbench.ajax_ignore_invite')
        band_member_count = BandMember.objects.count()
        
        # create an invitation
        invite = BandInvitation()
        invite.inviter = self.superjoe
        invite.band = self.superjoe.get_profile().solo_band
        invite.invitee = self.skiessi
        invite.save()

        # anonymous try to ignore it
        self.anonPostFail(ajax_ignore_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(BandInvitation.objects.count(), 1)
        self.assertEqual(BandMember.objects.count(), band_member_count)

        # wrong person try to ignore it
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(ajax_ignore_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.invitation_not_sent_to_you)
        self.assertEqual(BandInvitation.objects.count(), 1)
        self.assertEqual(BandMember.objects.count(), band_member_count)

        # correct person try to ignore it
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(ajax_ignore_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(BandInvitation.objects.count(), 0)
        self.assertEqual(BandMember.objects.count(), band_member_count)

    def test_accept_invite(self):
        ajax_accept_invite = reverse("workbench.ajax_accept_invite")
        band_member_count = BandMember.objects.count()
        outbox_count = len(mail.outbox)
        invitation_count = BandInvitation.objects.count()

        # create an invitation
        invite = BandInvitation()
        invite.inviter = self.superjoe
        invite.band = self.superjoe.get_profile().solo_band
        invite.invitee = self.skiessi
        invite.expire_date = datetime.now() + timedelta(days=1)
        invite.save()
        invitation_count += 1

        # try as anonymous 
        self.anonPostFail(ajax_accept_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(BandMember.objects.count(), band_member_count)
        self.assertEqual(BandInvitation.objects.count(), invitation_count)
        self.assertEqual(len(mail.outbox), outbox_count)

        # try as wrong person
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(ajax_accept_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.invitation_not_sent_to_you)
        self.assertEqual(BandMember.objects.count(), band_member_count)
        self.assertEqual(BandInvitation.objects.count(), invitation_count)
        self.assertEqual(len(mail.outbox), outbox_count)

        # try as correct person, after expired date
        self.client.login(username='skiessi', password='temp1234')

        invite.expire_date = datetime.now() - timedelta(days=1)
        invite.save()

        response = self.client.post(ajax_accept_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.invitation_expired)
        self.assertEqual(BandMember.objects.count(), band_member_count)
        self.assertEqual(BandInvitation.objects.count(), invitation_count)
        self.assertEqual(len(mail.outbox), outbox_count)

        # should work
        invite.expire_date = None
        invite.save()

        response = self.client.post(ajax_accept_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)

        band_member_count += 1
        outbox_count += 1
        invitation_count -= 1
        self.assertEqual(BandMember.objects.count(), band_member_count)
        self.assertEqual(BandInvitation.objects.count(), invitation_count)
        self.assertEqual(len(mail.outbox), outbox_count)

    def test_email_invite(self):
        ajax_email_invite = reverse("workbench.ajax_email_invite")
        ajax_accept_invite = reverse("workbench.ajax_accept_invite")
        outbox_count = len(mail.outbox)
        invite_count = BandInvitation.objects.count()

        # anonymously
        skiessi_solo = self.skiessi.get_profile().solo_band
        self.anonPostFail(ajax_email_invite, {
            'email': 'some.email@some.com',
            'band': skiessi_solo.id,
        })
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # invalid email address
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(ajax_email_invite, {
            'email': 'foo',
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.invalid_email_address)
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # invalid band
        response = self.client.post(ajax_email_invite, {
            'email': 'some.email@some.com',
            'band': 0,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_band_id)
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # band not owned by user
        response = self.client.post(ajax_email_invite, {
            'email': 'some.email@some.com',
            'band': self.superjoe.get_profile().solo_band.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.lack_permission_to_invite)
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # valid email address and band
        response = self.client.post(ajax_email_invite, {
            'email': 'some.email@some.com',
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        outbox_count += 1
        self.assertEqual(len(mail.outbox), outbox_count)
        invite_count += 1
        self.assertEqual(invite_count, BandInvitation.objects.count())
        invite = BandInvitation.objects.order_by('-pk')[0]
        self.assertEqual(invite.inviter.id, self.skiessi.id)
        self.assertEqual(invite.band.id, skiessi_solo.id)
        self.assertEqual(invite.role, BandMember.BAND_MEMBER)
        self.assertEqual(invite.isLink(), True)

        # email address of a registered user
        response = self.client.post(ajax_email_invite, {
            'email': self.superjoe.email,
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        outbox_count += 1
        self.assertEqual(len(mail.outbox), outbox_count)
        invite_count += 1
        self.assertEqual(invite_count, BandInvitation.objects.count())
        invite = BandInvitation.objects.order_by('-pk')[0]
        self.assertEqual(invite.inviter.id, self.skiessi.id)
        self.assertEqual(invite.band.id, skiessi_solo.id)
        self.assertEqual(invite.role, BandMember.BAND_MEMBER)
        self.assertEqual(invite.isLink(), False)
        self.assertEqual(invite.invitee.id, self.superjoe.id)

        # ...who has already been invited
        response = self.client.post(ajax_email_invite, {
            'email': self.superjoe.email,
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.already_invited_x_to_your_band.format(self.superjoe.username))
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # ...who is in the band already
        self.client.logout()
        self.client.login(username="superjoe", password="temp1234")
        response = self.client.post(ajax_accept_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        outbox_count += 1
        self.assertEqual(len(mail.outbox), outbox_count)
        invite_count -= 1
        self.assertEqual(invite_count, BandInvitation.objects.count())

        self.client.logout()
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.post(ajax_email_invite, {
            'email': self.superjoe.email,
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.x_already_in_band.format(self.superjoe.username))
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

    def test_invite_username(self):
        ajax_username_invite = reverse("workbench.ajax_username_invite")
        ajax_accept_invite = reverse("workbench.ajax_accept_invite")
        outbox_count = len(mail.outbox)
        invite_count = BandInvitation.objects.count()

        # anonymously
        skiessi_solo = self.skiessi.get_profile().solo_band
        self.anonPostFail(ajax_username_invite, {
            'username': self.superjoe.username,
            'band': skiessi_solo.id,
        })
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # nonexistant username
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(ajax_username_invite, {
            'username': "happy_unicorn_26",
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.that_user_does_not_exist)
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # invalid band
        response = self.client.post(ajax_username_invite, {
            'username': self.superjoe.username,
            'band': 0,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_band_id)
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # band not owned by user
        response = self.client.post(ajax_username_invite, {
            'username': self.superjoe.username,
            'band': self.just64helpin.get_profile().solo_band.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.lack_permission_to_invite)
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # valid username and band
        response = self.client.post(ajax_username_invite, {
            'username': self.superjoe.username,
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        outbox_count += 1
        self.assertEqual(len(mail.outbox), outbox_count)
        invite_count += 1
        self.assertEqual(invite_count, BandInvitation.objects.count())
        invite = BandInvitation.objects.order_by('-pk')[0]
        self.assertEqual(invite.inviter.id, self.skiessi.id)
        self.assertEqual(invite.band.id, skiessi_solo.id)
        self.assertEqual(invite.role, BandMember.BAND_MEMBER)
        self.assertEqual(invite.isLink(), False)
        self.assertEqual(invite.invitee.id, self.superjoe.id)

        # ...who has already been invited
        response = self.client.post(ajax_username_invite, {
            'username': self.superjoe.username,
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.already_invited_x_to_your_band.format(self.superjoe.username))
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())

        # ...who is in the band already
        self.client.logout()
        self.client.login(username="superjoe", password="temp1234")
        response = self.client.post(ajax_accept_invite, {
            'invitation': invite.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        outbox_count += 1
        self.assertEqual(len(mail.outbox), outbox_count)
        invite_count -= 1
        self.assertEqual(invite_count, BandInvitation.objects.count())

        self.client.logout()
        self.client.login(username="skiessi", password="temp1234")
        response = self.client.post(ajax_username_invite, {
            'username': self.superjoe.username,
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.x_already_in_band.format(self.superjoe.username))
        self.assertEqual(len(mail.outbox), outbox_count)
        self.assertEqual(invite_count, BandInvitation.objects.count())
        
    def test_redeem_invitation(self):
        redeem_invitation_url_name = 'workbench.redeem_invitation'
        invite_count = BandInvitation.objects.count()
        member_count = BandMember.objects.count()

        # anon
        self.checkLoginRedirect(reverse(redeem_invitation_url_name, args=['aoeu']))
        self.assertEqual(invite_count, BandInvitation.objects.count())
        self.assertEqual(member_count, BandMember.objects.count())

        # try with invalid hash
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.get(reverse(redeem_invitation_url_name, args=['aoeu']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err_msg'], True)
        self.assertEqual(invite_count, BandInvitation.objects.count())
        self.assertEqual(member_count, BandMember.objects.count())

        # invitation exists, but expired
        invite = BandInvitation()
        invite.inviter = self.skiessi
        invite.band = self.skiessi.get_profile().solo_band
        invite.expire_date = datetime.now() - timedelta(days=1)
        invite.code = create_hash(32)
        invite.count = 2
        invite.save()
        invite_count += 1

        response = self.client.get(reverse(redeem_invitation_url_name, args=[invite.code]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err_msg'], True)
        self.assertEqual(invite_count, BandInvitation.objects.count())
        self.assertEqual(member_count, BandMember.objects.count())

        # redeem good invitation
        invite.expire_date = None
        invite.save()

        response = self.client.get(reverse(redeem_invitation_url_name, args=[invite.code]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err_msg'], False)
        self.assertEqual(invite_count, BandInvitation.objects.count())
        invite = BandInvitation.objects.get(pk=invite.id)
        self.assertEqual(invite.count, 1)
        member_count += 1
        self.assertEqual(member_count, BandMember.objects.count())
        member = BandMember.objects.order_by('-pk')[0]
        self.assertEqual(member.user.id, self.just64helpin.id)
        self.assertEqual(member.band.id, self.skiessi.get_profile().solo_band.id)
        self.assertEqual(member.role, BandMember.BAND_MEMBER)

        # band member exists already
        response = self.client.get(reverse(redeem_invitation_url_name, args=[invite.code]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err_msg'], True)
        self.assertEqual(invite_count, BandInvitation.objects.count())
        self.assertEqual(member_count, BandMember.objects.count())
        
        # check that it deletes the invitation if the count is zero
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(reverse(redeem_invitation_url_name, args=[invite.code]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err_msg'], False)
        invite_count -= 1
        self.assertEqual(invite_count, BandInvitation.objects.count())
        member_count += 1
        self.assertEqual(member_count, BandMember.objects.count())
        member = BandMember.objects.order_by('-pk')[0]
        self.assertEqual(member.user.id, self.superjoe.id)
        self.assertEqual(member.band.id, self.skiessi.get_profile().solo_band.id)
        self.assertEqual(member.role, BandMember.BAND_MEMBER)

    def test_create_band(self):
        ajax_create_band = reverse("workbench.ajax_create_band")
        band_count = Band.objects.count()

        # anonymous
        self.anonPostFail(ajax_create_band, {
            'band_name': 'The Burning Awesome',
        })
        self.assertEqual(band_count, Band.objects.count())

        # a band with a friggin long name
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(ajax_create_band, {
            'band_name': 'a' * 101,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(band_count, Band.objects.count())

        # normal case which should work
        response = self.client.post(ajax_create_band, {
            'band_name': 'The Burning Awesome',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        band_count += 1
        self.assertEqual(band_count, Band.objects.count())
        
        # doesn't have any bands left in account
        prof = self.just64helpin.get_profile()
        prof.band_count_limit = 2
        prof.save()
        response = self.client.post(ajax_create_band, {
            'band_name': 'Octopus',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(band_count, Band.objects.count())

    def test_project_filters(self):
        ajax_project_filters = reverse("workbench.ajax_project_filters")

        # anon
        skiessi_solo = self.skiessi.get_profile().solo_band
        self.anonGetFail(ajax_project_filters, {
            'band': skiessi_solo.id,
        })

        # bogus band
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(ajax_project_filters, {
            'band': 0,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_band_id)

        # band not owned by user
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(ajax_project_filters, {
            'band': self.superjoe.get_profile().solo_band.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_work_on_this_band)

        # valid request
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(ajax_project_filters, {
            'band': skiessi_solo.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)

    def test_ajax_project(self):
        ajax_project = reverse("workbench.ajax_project")

        self.setUpTBA()
        the_castle = Project.objects.get(title='The Castle')

        # anon access open source band
        # TODO

        # anon access private band
        self.client.logout()
        response = self.client.get(ajax_project, {
            'last_version': 'null',
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_authenticated)

        # someone not in band access private band
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.get(ajax_project, {
            'last_version': 'null',
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_critique_this_band)

        # project that doesn't exist
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(ajax_project, {
            'last_version': 'null',
            'project': 113,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_project_id)

        # legit project, get all versions
        response = self.client.get(ajax_project, {
            'last_version': 'null',
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['project']['id'], the_castle.id)
        self.assertEqual(data['user']['has_permission'], True)
        self.assertEqual(data['user']['is_authenticated'], True)
        self.assertEqual(len(data['versions']), 1)

        # legit project, get versions since the only one (should return none)
        response = self.client.get(ajax_project, {
            'last_version': the_castle.latest_version.id,
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['project']['id'], the_castle.id)
        self.assertEqual(data['user']['has_permission'], True)
        self.assertEqual(data['user']['is_authenticated'], True)
        self.assertEqual(len(data['versions']), 0)

    def test_project_list(self):
        ajax_project_list = reverse("workbench.ajax_project_list")

        self.setUpTBA()
        tba = Band.objects.get(title='The Burning Awesome')
        the_castle = Project.objects.get(title='The Castle')

        # anon
        self.anonGetFail(ajax_project_list, {
            'band': tba.id,
        })

        # try to access list from other private band
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.get(ajax_project_list, {
            'band': tba.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_critique_this_band)

        # list all contents
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(ajax_project_list, {
            'band': tba.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['data']['projects']), 2)

        # test paging
        # TODO

        # test filter
        # TODO

        # test search
        response = self.client.get(ajax_project_list, {
            'band': tba.id,
            'search': 'astl he',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['data']['projects']), 1)
        self.assertEqual(data['data']['projects'][0]['id'], the_castle.id)

    def test_upload_samples(self):
        ajax_upload_samples = reverse("workbench.ajax_upload_samples")
        create_project_url = lambda band_id: reverse("workbench.create_project", args=[band_id])

        self.setUpTBA()
        uploaded_sample_count = UploadedSample.objects.count()
        sample_dependency_count = SampleDependency.objects.count()
        tba = Band.objects.get(title="The Burning Awesome")
        superjoe_solo = self.superjoe.get_profile().solo_band

        # upload a project to The Burning Awesome that depends on a.wav and is missing samples
        self.client.login(username='superjoe', password='temp1234')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'),'rb')
        project_file = open(absolute('fixtures/depends-a.flp'),'rb')
        response = self.client.post(create_project_url(tba.id), {
            'title': "A",
            'file_source': project_file,
            'file_mp3':  mp3_file,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        sample_dependency_count += 1
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())

        # upload a project to superjoe solo band that depends on b.wav and is missing samples
        project_file = open(absolute('fixtures/depends-b.flp'),'rb')
        response = self.client.post(create_project_url(superjoe_solo.id), {
            'title': "B",
            'file_source': project_file,
        })
        self.assertEqual(response.status_code, 302)
        sample_dependency_count += 1
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

        # anon
        sample_file_count = SampleFile.objects.count()
        self.client.logout()
        sample_c = open(absolute('fixtures/c.wav'), 'rb')
        sample_d = open(absolute('fixtures/d.wav'), 'rb')
        self.anonPostFail(ajax_upload_samples, {
            'band': tba.id,
            'file': [sample_c, sample_d],
        })
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

        # bogus band
        self.client.login(username='just64helpin', password='temp1234')
        sample_c = open(absolute('fixtures/c.wav'), 'rb')
        sample_d = open(absolute('fixtures/d.wav'), 'rb')
        response = self.client.post(ajax_upload_samples, {
            'band': 0,
            'file': [sample_c, sample_d],
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_band_id)
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

        # not a band member
        self.client.login(username='just64helpin', password='temp1234')
        sample_c = open(absolute('fixtures/c.wav'), 'rb')
        sample_d = open(absolute('fixtures/d.wav'), 'rb')
        response = self.client.post(ajax_upload_samples, {
            'band': tba.id,
            'file': [sample_c, sample_d],
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_work_on_this_band)
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

        # band member but without edit permission
        # TODO

        # upload 3 samples. 1 of them this band is missing. 1 of them another
        # of the user's bands is missing. the SampleDependency should be filled out.
        dependency_a = SampleDependency.objects.get(title='a.wav')
        dependency_b = SampleDependency.objects.get(title='b.wav')
        self.assertEqual(dependency_a.uploaded_sample, None)
        self.assertEqual(dependency_b.uploaded_sample, None)
        self.client.login(username='superjoe', password='temp1234')
        sample_a = open(absolute('fixtures/a.wav'), 'rb')
        sample_b = open(absolute('fixtures/b.wav'), 'rb')
        sample_c = open(absolute('fixtures/c.wav'), 'rb')
        response = self.client.post(ajax_upload_samples, {
            'band': tba.id,
            'file': [sample_a, sample_b, sample_c],
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        sample_file_count += 3
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        dependency_a = SampleDependency.objects.get(title='a.wav')
        dependency_b = SampleDependency.objects.get(title='b.wav')
        uploaded_sample_a = UploadedSample.objects.get(title='a.wav')
        uploaded_sample_b = UploadedSample.objects.get(title='b.wav')
        self.assertEqual(dependency_a.uploaded_sample.id, uploaded_sample_a.id)
        self.assertEqual(dependency_b.uploaded_sample.id, uploaded_sample_b.id)
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())
        uploaded_sample_count += 3
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

        # upload 2 samples in a .zip file. one of the samples we already have uploaded.
        # should only create 1 new SampleFile
        sample_a = open(absolute('fixtures/a.wav'), 'rb')
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        response = self.client.post(ajax_upload_samples, {
            'band': tba.id,
            'file': [cd_zip, sample_a],
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        sample_file_count += 1
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        uploaded_sample_count += 1
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

        # corrupt .zip file
        corrupt_zip = open(absolute('fixtures/corrupt.zip'), 'rb')
        response = self.client.post(ajax_upload_samples, {
            'band': tba.id,
            'file': corrupt_zip,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

        # upload same samples as a different user and make sure that no new SampleFiles are generated
        self.client.login(username='just64helpin', password='temp1234')
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        response = self.client.post(ajax_upload_samples, {
            'band': self.just64helpin.get_profile().solo_band.id,
            'file': cd_zip,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(sample_dependency_count, SampleDependency.objects.count())
        uploaded_sample_count += 2
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())

    def test_upload_samples_as_version(self):
        ajax_upload_samples_as_version = reverse("workbench.ajax_upload_samples_as_version")

        self.setUpTBA()
        the_castle = Project.objects.get(title='The Castle')
        sample_file_count = SampleFile.objects.count()
        uploaded_sample_count = UploadedSample.objects.count()
        version_count = ProjectVersion.objects.count()

        # anon
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        self.anonPostFail(ajax_upload_samples_as_version, {
            'project': the_castle.id,
            'comments': "uploaded samples comments",
            'file': cd_zip,
        })
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())

        # bogus project
        self.client.login(username='just64helpin', password='temp1234')
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        response = self.client.post(ajax_upload_samples_as_version, {
            'project': 0,
            'comments': "uploaded samples comments",
            'file': cd_zip,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_project_id)
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())

        # not in band
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        response = self.client.post(ajax_upload_samples_as_version, {
            'project': the_castle.id,
            'comments': "uploaded samples comments",
            'file': cd_zip,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_work_on_this_band)
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())

        # in band but not edit permission
        # TODO

        # upload 2 samples
        self.client.login(username='superjoe', password='temp1234')
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        self.client.post(ajax_upload_samples_as_version, {
            'project': the_castle.id,
            'comments': "uploaded samples comments",
            'file': cd_zip,
        })
        sample_file_count += 2
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        uploaded_sample_count += 2
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        version = ProjectVersion.objects.order_by('-pk')[0]
        self.assertEqual(version.comment_node.content, "uploaded samples comments")
        self.assertEqual(version.provided_samples.count(), 2)
        
    def test_rename_project(self):
        ajax_rename_project = reverse("workbench.ajax_rename_project")

        self.setUpTBA()
        version_count = ProjectVersion.objects.count()
        the_castle = Project.objects.get(title='The Castle')

        # anon
        self.anonPostFail(ajax_rename_project, {
            'project': the_castle.id,
            'title': "The Castle LOL",
            'comments': 'comments1',
        })
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.title, 'The Castle')
        self.assertEqual(version_count, ProjectVersion.objects.count())

        # bogus project
        self.client.login(username='just64helpin', password='temp1234')
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        response = self.client.post(ajax_rename_project, {
            'project': 0,
            'title': "The Castle LOL",
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_project_id)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.title, 'The Castle')
        self.assertEqual(version_count, ProjectVersion.objects.count())

        # not in band
        response = self.client.post(ajax_rename_project, {
            'project': the_castle.id,
            'title': "The Castle LOL",
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_work_on_this_band)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.title, 'The Castle')
        self.assertEqual(version_count, ProjectVersion.objects.count())

        # in band, but don't have edit permission
        # TODO

        # too long of a name
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_rename_project, {
            'project': the_castle.id,
            'title': 'a' * 101,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.title, 'The Castle')
        self.assertEqual(version_count, ProjectVersion.objects.count())

        # ok
        response = self.client.post(ajax_rename_project, {
            'project': the_castle.id,
            'title': "The Castle LOL",
            'comments': "I thought this would be a good idea.",
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.title, 'The Castle LOL')
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())

    def test_dependency_ownership(self):
        ajax_dependency_ownership = reverse("workbench.ajax_dependency_ownership")

        self.setUpTBA()

        plugin = PluginDepenency.objects.all()[0]
        studio = Studio.objects.all()[0]
        prof = self.just64helpin.get_profile()
        prof.plugins.clear()
        prof.studios.clear()
        prof.save()

        # anon
        self.anonPostFail(ajax_dependency_ownership, {
            'dependency_type': PluginDepenency.STUDIO,
            'dependency_id': studio.id,
            'have': 'true',
        })
        prof = Profile.objects.get(pk=prof.id)
        self.assertEqual(prof.plugins.count(), 0)
        self.assertEqual(prof.studios.count(), 0)

        # bogus
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(ajax_dependency_ownership, {
            'dependency_type': PluginDepenency.STUDIO,
            'dependency_id': 0,
            'have': 'true',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_dependency_id)

        # say we have a plugin
        response = self.client.post(ajax_dependency_ownership, {
            'dependency_type': PluginDepenency.EFFECT,
            'dependency_id': plugin.id,
            'have': 'true',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        prof = Profile.objects.get(pk=prof.id)
        self.assertEqual(prof.plugins.count(), 1)
        self.assertEqual(prof.studios.count(), 0)

        # say we don't have a plugin
        response = self.client.post(ajax_dependency_ownership, {
            'dependency_type': PluginDepenency.EFFECT,
            'dependency_id': plugin.id,
            'have': 'false',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        prof = Profile.objects.get(pk=prof.id)
        self.assertEqual(prof.plugins.count(), 0)
        self.assertEqual(prof.studios.count(), 0)

        # say we have a studio
        response = self.client.post(ajax_dependency_ownership, {
            'dependency_type': PluginDepenency.STUDIO,
            'dependency_id': studio.id,
            'have': 'true',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        prof = Profile.objects.get(pk=prof.id)
        self.assertEqual(prof.plugins.count(), 0)
        self.assertEqual(prof.studios.count(), 1)

        # say we don't have a studio
        response = self.client.post(ajax_dependency_ownership, {
            'dependency_type': PluginDepenency.STUDIO,
            'dependency_id': studio.id,
            'have:': 'false',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        prof = Profile.objects.get(pk=prof.id)
        self.assertEqual(prof.plugins.count(), 0)
        self.assertEqual(prof.studios.count(), 0)

    def test_provide_project(self):
        ajax_provide_project = reverse("workbench.ajax_provide_project")

        # set up the db so that there is a project without a project
        self.setUpTBA()
        the_castle = Project.objects.get(title='The Castle')
        castle_song = the_castle.latest_version.song
        castle_song.source_file = ""
        castle_song.save()

        # anon
        project_file = open(absolute('fixtures/blank.flp'), 'rb')
        self.anonPostFail(ajax_provide_project, {
            'version': the_castle.latest_version.id,
            'file': project_file,
        })
        castle_song = Song.objects.get(pk=castle_song.id)
        self.assertEqual(castle_song.source_file, "")

        # bogus version
        self.client.login(username='skiessi', password='temp1234')
        project_file = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(ajax_provide_project, {
            'version': 0,
            'file': project_file,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_version_id)
        castle_song = Song.objects.get(pk=castle_song.id)
        self.assertEqual(castle_song.source_file, "")

        # don't have edit permission
        self.client.login(username='just64helpin', password='temp1234')
        project_file = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(ajax_provide_project, {
            'version': the_castle.latest_version.id,
            'file': project_file,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_work_on_this_band)
        castle_song = Song.objects.get(pk=castle_song.id)
        self.assertEqual(castle_song.source_file, "")

        # ok
        self.client.login(username='skiessi', password='temp1234')
        project_file = open(absolute('fixtures/blank.flp'), 'rb')
        response = self.client.post(ajax_provide_project, {
            'version': the_castle.latest_version.id,
            'file': project_file,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        castle_song = Song.objects.get(pk=castle_song.id)
        self.assertNotEqual(castle_song.source_file, "")

    def test_provide_mp3(self):
        ajax_provide_mp3 = reverse("workbench.ajax_provide_mp3")
        create_project_url = lambda band_id: reverse("workbench.create_project", args=[band_id])

        superjoe_solo = self.superjoe.get_profile().solo_band

        # create a project without mp3 to add it later
        self.client.login(username='superjoe', password='temp1234')
        project_file = open(absolute('fixtures/blank.flp'),'rb')
        response = self.client.post(create_project_url(superjoe_solo.id), {
            'title': "Blank",
            'file_source': project_file,
        })
        self.assertEqual(response.status_code, 302)
        project = Project.objects.order_by('-pk')[0]
        project_song = project.latest_version.song

        # anon
        blank_mp3file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'),'rb')
        self.anonPostFail(ajax_provide_mp3, {
            'version': project.latest_version.id,
            'file': blank_mp3file,
        })
        project_song = Song.objects.get(pk=project_song.id)
        self.assertEqual(project_song.mp3_file, "")

        # don't have edit permission
        self.client.login(username='just64helpin', password='temp1234')
        blank_mp3file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'),'rb')
        response = self.client.post(ajax_provide_mp3, {
            'version': project.latest_version.id,
            'file': blank_mp3file,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_work_on_this_band)
        project_song = Song.objects.get(pk=project_song.id)
        self.assertEqual(project_song.mp3_file, "")

        # corrupt mp3
        self.client.login(username='superjoe', password='temp1234')
        blank_mp3file = open(absolute('fixtures/corrupt.mp3'),'rb')
        response = self.client.post(ajax_provide_mp3, {
            'version': project.latest_version.id,
            'file': blank_mp3file,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.invalid_mp3_file)
        project_song = Song.objects.get(pk=project_song.id)
        self.assertEqual(project_song.mp3_file, "")

        # ok
        self.client.login(username='superjoe', password='temp1234')
        blank_mp3file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'),'rb')
        response = self.client.post(ajax_provide_mp3, {
            'version': project.latest_version.id,
            'file': blank_mp3file,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        project_song = Song.objects.get(pk=project_song.id)
        self.assertNotEqual(project_song.mp3_file, "")

    def test_checkout(self):
        ajax_checkout = reverse("workbench.ajax_checkout")

        self.setUpTBA()
        the_castle = Project.objects.get(title="The Castle")

        # anon
        self.anonPostFail(ajax_checkout, {
            'project': the_castle.id,
        })
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.checked_out_to, None)

        # bogus project
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': 0,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_project_id)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.checked_out_to, None)

        # not a band member
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.you_dont_have_permission_to_work_on_this_band)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.checked_out_to, None)

        # band member but don't have edit permission
        # TODO

        # ok
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.checked_out_to.id, self.superjoe.id)

        # already checked out
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.this_project_already_checked_out)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.checked_out_to.id, self.superjoe.id)

    def test_checkin(self):
        ajax_checkin = reverse("workbench.ajax_checkin")
        ajax_checkout = reverse("workbench.ajax_checkout")

        # set up a band and stuff
        self.setUpTBA()
        the_castle = Project.objects.get(title='The Castle')

        dependency_count = SampleDependency.objects.count()
        uploaded_sample_count = UploadedSample.objects.count()
        sample_file_count = SampleFile.objects.count()
        version_count = ProjectVersion.objects.count()

        # superjoe check out the castle
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)

        # anon
        self.client.logout()
        project_file = open(absolute('fixtures/depends-a.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        self.anonPostFail(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'comments1234',
        })
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())

        # bogus project
        self.client.login(username='superjoe', password='temp1234')
        project_file = open(absolute('fixtures/depends-a.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': 0,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'comments1234',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.bad_project_id)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())

        # not in band
        self.client.login(username='just64helpin', password='temp1234')
        project_file = open(absolute('fixtures/depends-a.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'comments1234',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_checked_out_to_you)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())

        # band member but don't have edit permission
        # TODO

        # someone else has it checked out
        self.client.login(username='skiessi', password='temp1234')
        project_file = open(absolute('fixtures/depends-a.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'comments1234',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_checked_out_to_you)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())

        # just check in
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        the_castle = Project.objects.get(pk=the_castle.id)
        self.assertEqual(the_castle.checked_out_to, None)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())

        # re-check out
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)

        # missing project file (should not work)
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'mp3_preview': mp3_file,
            'comments': 'comments1234',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.must_submit_project_file)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())

        # missing mp3 file, and comment field (should work)
        project_file = open(absolute('fixtures/depends-a.flp'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        dependency_count += 1
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        depend = SampleDependency.objects.order_by('-pk')[0]
        self.assertEqual(depend.title, 'a.wav')
        self.assertEqual(depend.uploaded_sample, None)
        self.assertNotEqual(depend.song.comment_node, None)

        # not checked out
        project_file = open(absolute('fixtures/depends-a.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'comments1234',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['reason'], design.not_checked_out_to_you)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())

        # re-check out
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)

        # supply everything. LMMS project .mmpz
        # there should be missing sample files
        project_file = open(absolute('fixtures/depends-clap01.mmpz'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'comments1234',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        dependency_count += 1
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        depend = SampleDependency.objects.order_by('-pk')[0]
        self.assertEqual(depend.title, 'clap01.ogg')
        self.assertEqual(depend.uploaded_sample, None)
        self.assertEqual(depend.song.comment_node.content, "comments1234")

        # re-check out
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)

        # supply everything. LMMS project .mmp
        # same dependency so should not add any dependencies.
        project_file = open(absolute('fixtures/depends-clap01.mmp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'abc123',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(Song.objects.order_by('-pk')[0].comment_node.content, "abc123")

        # re-check out
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)

        # supply everything. unknown project
        # should not break anything, but also should not create sample files
        project_file = open(absolute('fixtures/unknown-studio.xyz'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'unknown studio wtf',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(Song.objects.order_by('-pk')[0].comment_node.content, "unknown studio wtf")

        # re-check out
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)

        # supply everything, FL Studio project, including samples in .zip
        # should make all missing samples resolved
        project_file = open(absolute('fixtures/a.flp.zip'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'ah much better',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        dependency_count += 1
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        uploaded_sample_count += 1
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        sample_file_count += 1
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(Song.objects.order_by('-pk')[0].comment_node.content, "ah much better")
        dep = SampleDependency.objects.filter(title='a.wav').order_by('-pk')[0]
        self.assertEqual(dep.uploaded_sample.id, UploadedSample.objects.order_by('-pk')[0].id)

        # re-check out
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.post(ajax_checkout, {
            'project': the_castle.id,
        })
        self.assertEqual(response.status_code, 200)

        # supply everything, unknown project, including samples in .zip
        # should add samples from zip but leave the .zip file as the project file.
        project_file = open(absolute('fixtures/unknown-studio-ef.zip'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(ajax_checkin, {
            'project': the_castle.id,
            'project_file': project_file,
            'mp3_preview': mp3_file,
            'comments': 'unknown studio zip',
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['success'], True)
        self.assertEqual(dependency_count, SampleDependency.objects.count())
        version_count += 1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        uploaded_sample_count += 3 # we're counting the studio here.
        self.assertEqual(uploaded_sample_count, UploadedSample.objects.count())
        sample_file_count += 3
        self.assertEqual(sample_file_count, SampleFile.objects.count())
        self.assertEqual(Song.objects.order_by('-pk')[0].comment_node.content, "unknown studio zip")

    def test_create(self):
        """url(r'^create/$', 'workshop.views.create_band', name="workbench.create_band"),"""
        create_url = reverse('workbench.create_band')
        band_count = Band.objects.count()

        # anon
        self.checkLoginRedirect(create_url)
        self.assertEqual(band_count, Band.objects.count())

        # too long a name
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.post(create_url, {
            'band_name': 'a' * 101,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(band_count, Band.objects.count())

        # normal case which should work
        response = self.client.post(create_url, {
            'band_name': 'JH Sounds',
        })
        self.assertRedirects(response, reverse('workbench.home'))
        band_count += 1
        self.assertEqual(band_count, Band.objects.count())

        # doesn't have any bands left in account
        prof = self.just64helpin.get_profile()
        prof.band_count_limit = 2
        prof.save()
        response = self.client.post(create_url, {
            'band_name': 'OMGZOMB',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(band_count, Band.objects.count())

    def test_band(self):
        self.staticPage(reverse('workbench.band', args=[self.skiessi.get_profile().solo_band.id]))
        self.staticPage(reverse('workbench.band', args=[self.superjoe.get_profile().solo_band.id]))
        self.staticPage(reverse('workbench.band', args=[self.just64helpin.get_profile().solo_band.id]))

    def test_band_settings(self):
        """url(r'^band/(\d+)/settings/$', 'workshop.views.band_settings', name="workbench.band_settings"),"""
        band_settings_url_name = 'workbench.band_settings'
        # TODO

    def test_create_project(self):
        """url(r'^band/(\d+)/create/$', 'workshop.views.create_project', name="workbench.create_project"),"""
        create_project_url = lambda band_id: reverse('workbench.create_project', args=[band_id])

        project_count = Project.objects.count()
        version_count = ProjectVersion.objects.count()
        plugin_deps_count = PluginDepenency.objects.count()
        
        skiessi_solo = self.skiessi.get_profile().solo_band
        # anon
        self.checkLoginRedirect(create_project_url(skiessi_solo.id))

        # bogus band
        self.client.login(username='skiessi', password='temp1234')
        project_file = open(absolute('fixtures/4frontpiano.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(create_project_url(0), {
            'title': 'Front',
            'file_source': project_file,
            'file_mp3': mp3_file,
            'comments': 'abc123',
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(project_count, Project.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(plugin_deps_count, PluginDepenency.objects.count())

        # not in band
        self.client.login(username='just64helpin', password='temp1234')
        project_file = open(absolute('fixtures/4frontpiano.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(create_project_url(skiessi_solo.id), {
            'title': 'Front',
            'file_source': project_file,
            'file_mp3': mp3_file,
            'comments': 'abc123',
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(project_count, Project.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(plugin_deps_count, PluginDepenency.objects.count())

        # leave out project file (should not work)
        self.client.login(username='skiessi', password='temp1234')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(create_project_url(skiessi_solo.id), {
            'title': 'Front',
            'file_mp3': mp3_file,
            'comments': 'abc123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'file_source', design.this_field_is_required)
        self.assertEqual(project_count, Project.objects.count())
        self.assertEqual(version_count, ProjectVersion.objects.count())
        self.assertEqual(plugin_deps_count, PluginDepenency.objects.count())

        # leave out mp3 and comments (should work)
        project_file = open(absolute('fixtures/4frontpiano.flp'), 'rb')
        response = self.client.post(create_project_url(skiessi_solo.id), {
            'title': 'Front',
            'file_source': project_file,
        })
        self.assertEqual(response.status_code, 302)
        project_count += 1
        self.assertEqual(project_count, Project.objects.count())
        version_count +=  1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        project = Project.objects.order_by('-pk')[0]
        version = ProjectVersion.objects.order_by('-pk')[0]
        self.assertEqual(version.project.id, project.id)
        self.assertEqual(version.version, 1)
        self.assertNotEqual(version.song.comment_node, None)
        plugin_deps_count += 1
        self.assertEqual(plugin_deps_count, PluginDepenency.objects.count())
        plugin = PluginDepenency.objects.order_by('-pk')[0]
        self.assertEqual(plugin.title, '4Front Piano')
        song = version.song
        self.assertEqual(song.plugins.all()[0].id, plugin.id)
        
        # supply everything
        project_file = open(absolute('fixtures/4frontpiano.flp'), 'rb')
        mp3_file = open(absolute('fixtures/silence10s-flstudio-tags.mp3'), 'rb')
        response = self.client.post(create_project_url(skiessi_solo.id), {
            'title': 'Front',
            'file_source': project_file,
            'file_mp3': mp3_file,
            'comments': 'I have been writing tests for 9 hours.',
        })
        self.assertEqual(response.status_code, 302)
        project_count += 1
        self.assertEqual(project_count, Project.objects.count())
        version_count +=  1
        self.assertEqual(version_count, ProjectVersion.objects.count())
        project = Project.objects.order_by('-pk')[0]
        version = ProjectVersion.objects.order_by('-pk')[0]
        self.assertEqual(version.project.id, project.id)
        self.assertEqual(version.version, 1)
        self.assertNotEqual(version.song.comment_node, None)
        self.assertEqual(plugin_deps_count, PluginDepenency.objects.count())
        self.assertEqual(version.song.comment_node.content, 'I have been writing tests for 9 hours.')

    def test_project(self):
        self.setUpTBA()
        tba = Band.objects.get(title='The Burning Awesome')
        the_castle = Project.objects.get(title='The Castle')
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(reverse('workbench.project', args=[tba.id, the_castle.id]))
        self.assertEqual(response.status_code, 200)

    def test_band_invite(self):
        self.setUpTBA()
        tba = Band.objects.get(title='The Burning Awesome')
        self.client.login(username='skiessi', password='temp1234')
        response = self.client.get(reverse('workbench.band_invite', args=[tba.id]))
        self.assertEqual(response.status_code, 200)

    def test_download_zip(self):
        download_zip_url = reverse('workbench.download_zip')
        create_project_url = lambda band_id: reverse('workbench.create_project', args=[band_id])

        # upload a project with a bunch of samples
        superjoe_solo = self.superjoe.get_profile().solo_band
        self.client.login(username='superjoe', password='temp1234')
        project_file = open(absolute('fixtures/depends-abcdef.zip'),'rb')
        response = self.client.post(create_project_url(superjoe_solo.id), {
            'title': "Blank",
            'file_source': project_file,
        })
        self.assertEqual(response.status_code, 302)

        song = Song.objects.order_by('-pk')[0]
        
        # anon
        self.client.logout()
        self.checkLoginRedirect(download_zip_url)

        # bogus song
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(download_zip_url, {
            'song': 13,
        })
        self.assertEqual(response.status_code, 404)

        # not in band
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.get(download_zip_url, {
            'song': song.id,
        })
        self.assertEquals(response.status_code, 403)

        # in band but not permission to view
        # TODO

        # we want everything
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(download_zip_url, {
            'song': song.id,
        })
        self.assertEquals(response['Content-Type'], 'application/zip')
        # TODO: check that the samples made it into the zip OK

        # sneak in an id of a SampleDependency which shouldn't have access to
        # TODO

        # normal case
        sample_deps = []
        sample_deps.append(SampleDependency.objects.get(title='a.wav'))
        sample_deps.append(SampleDependency.objects.get(title='c.wav'))
        sample_deps.append(SampleDependency.objects.get(title='e.wav'))
        response = self.client.get(download_zip_url, {
            'song': song.id,
            's': sample_deps,
        })
        self.assertEquals(response['Content-Type'], 'application/zip')
        # TODO: check that the samples made it into the zip OK

    def test_download_sample(self):
        download_sample_url = lambda uploaded_sample_id, sample_title: reverse('workbench.download_sample', args=[uploaded_sample_id, sample_title])
        create_project_url = lambda band_id: reverse('workbench.create_project', args=[band_id])

        # upload a project with a bunch of samples
        superjoe_solo = self.superjoe.get_profile().solo_band
        self.client.login(username='superjoe', password='temp1234')
        project_file = open(absolute('fixtures/depends-abcdef.zip'),'rb')
        response = self.client.post(create_project_url(superjoe_solo.id), {
            'title': "Blank",
            'file_source': project_file,
        })
        self.assertEqual(response.status_code, 302)

        sample = UploadedSample.objects.get(title='c.wav')
        sample_hash = file_hash(absolute('fixtures/c.wav'))

        # anon
        self.client.logout()
        self.checkLoginRedirect(download_sample_url(sample.id, 'monkey.wav'))

        # not authorized to get sample
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.get(download_sample_url(sample.id, 'monkey.wav'))
        self.assertEquals(response.status_code, 403)

        # bogus sample 
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(download_sample_url(1337, 'monkey.wav'))
        self.assertEquals(response.status_code, 404)

        # ok
        response = self.client.get(download_sample_url(sample.id, 'monkey.wav'))
        md5 = hashlib.md5(response.content)
        self.assertEquals(md5.hexdigest(), sample_hash)

    def test_download_sample_zip(self):
        download_sample_zip_url = reverse('workbench.download_sample_zip')
        ajax_upload_samples_as_version = reverse("workbench.ajax_upload_samples_as_version")

        self.setUpTBA()
        the_castle = Project.objects.get(title='The Castle')

        # skiessi provide samples as version
        self.client.login(username='skiessi', password='temp1234')
        cd_zip = open(absolute('fixtures/samples-cd.zip'), 'rb')
        self.verifyAjax(self.client.post(ajax_upload_samples_as_version, {
            'project': the_castle.id,
            'file': cd_zip,
        }))
        sample = UploadedSample.objects.get(title='c.wav')

        # anon
        self.client.logout()
        self.checkLoginRedirect(download_sample_zip_url)

        # just64helpin try to get one of skiessi's samples
        self.client.login(username='just64helpin', password='temp1234')
        response = self.client.get(download_sample_zip_url, {
            's': sample.id,
        })
        self.assertEqual(response.status_code, 403)

        # ok
        self.client.login(username='superjoe', password='temp1234')
        response = self.client.get(download_sample_zip_url, {
            's': UploadedSample.objects.all(),
        })
        self.assertEqual(response['Content-Type'], 'application/zip')

    def test_plugin(self):
        self.setUpTBA()
        plugin = PluginDepenency.objects.all()[0]
        self.staticPage(reverse('workbench.plugin', args=[plugin.url]))

    def test_studio(self):
        self.staticPage(reverse('workbench.studio', args=['flstudio']))
        self.staticPage(reverse('workbench.studio', args=['lmms']))
