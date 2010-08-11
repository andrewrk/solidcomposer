from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from main.models import BandMember, Band, Profile
from main.tests import commonSetUp, commonTearDown
from django.contrib.auth.models import User

from workshop.models import BandInvitation, Project, ProjectVersion, PluginDepenency, Studio
from workshop import syncdaw
from workshop import design

import simplejson as json
from datetime import datetime, timedelta

from main.common import create_hash

import os

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
                'agree_to_terms': True
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

    def test_upload_samples_as_version(self):
        ajax_upload_samples_as_version = reverse("workbench.ajax_upload_samples_as_version")
        
    def test_rename_project(self):
        ajax_rename_project = reverse("workbench.ajax_rename_project")

    def test_dependency_ownership(self):
        ajax_dependency_ownership = reverse("workbench.ajax_dependency_ownership")

    def test_provide_project(self):
        ajax_provide_project = reverse("workbench.ajax_provide_project")

    def test_provide_mp3(self):
        ajax_provide_mp3 = reverse("workbench.ajax_provide_mp3")

    def test_checkout(self):
        ajax_checkout = reverse("workbench.ajax_checkout")

    def test_checkin(self):
        ajax_checkin = reverse("workbench.ajax_checkin")

    def test_create(self):
        """url(r'^create/$', 'workshop.views.create_band', name="workbench.create_band"),"""
        pass

    def test_band(self):
        self.staticPage(reverse('workbench.band', args=[self.skiessi.get_profile().solo_band.id]))
        self.staticPage(reverse('workbench.band', args=[self.superjoe.get_profile().solo_band.id]))
        self.staticPage(reverse('workbench.band', args=[self.just64helpin.get_profile().solo_band.id]))

    def test_band_settings(self):
        """url(r'^band/(\d+)/settings/$', 'workshop.views.band_settings', name="workbench.band_settings"),"""
        pass

    def test_band_settings_space(self):
        """url(r'^band/(\d+)/settings/space/$', 'workshop.views.band_settings_space', name="workbench.band_settings_space"),"""
        pass

    def test_create_project(self):
        """url(r'^band/(\d+)/create/$', 'workshop.views.create_project', name="workbench.create_project"),"""
        pass

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
        """url(r'^download/zip/$', 'workshop.views.download_zip', name="workbench.download_zip"),"""
        pass

    def test_download_sample(self):
        """url(r'^download/sample/(\d+)/(.+)/$', 'workshop.views.download_sample', name="workbench.download_sample"),"""
        pass

    def test_download_sample_zip(self):
        """url(r'^download/samples/$', 'workshop.views.download_sample_zip', name="workbench.download_sample_zip"),"""
        pass

    def test_plugin(self):
        self.setUpTBA()
        plugin = PluginDepenency.objects.all()[0]
        self.staticPage(reverse('workbench.plugin', args=[plugin.url]))

    def test_studio(self):
        self.staticPage(reverse('workbench.studio', args=['flstudio']))
        self.staticPage(reverse('workbench.studio', args=['lmms']))
