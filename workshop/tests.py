from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from main.models import BandMember
from main.tests import commonSetUp, commonTearDown
from django.contrib.auth.models import User

from workshop.models import BandInvitation
from workshop import design

import simplejson as json
from datetime import datetime, timedelta

class SimpleTest(TestCase):
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

    def tearDown(self):
        commonTearDown(self)

    def staticPage(self, url_name):
        "tests if the page doesn't error out logged in and logged out."
        url = reverse(url_name)
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

    def test_home(self):
        return self.staticPage('workbench.home')
        
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
        """url(r'^redeem/(.+)/$', 'workshop.views.redeem_invitation', name="workbench.redeem_invitation"),"""
        pass

    def test_create_band(self):
        """url(r'^ajax/create_band/$', 'workshop.views.ajax_create_band', name="workbench.ajax_create_band"),"""
        pass
        
    def test_project_filters(self):
        """url(r'^ajax/project_filters/$', 'workshop.views.ajax_project_filters', name="workbench.ajax_project_filters"),"""
        pass

    def test_project(self):
        """url(r'^ajax/project/$', 'workshop.views.ajax_project', name="workbench.ajax_project"),"""
        pass

    def test_project_list(self):
        """url(r'^ajax/project_list/$', 'workshop.views.ajax_project_list', name="workbench.ajax_project_list"),"""
        pass

    def test_upload_samples(self):
        """url(r'^ajax/upload_samples/$', 'workshop.views.ajax_upload_samples', name="workbench.ajax_upload_samples"),"""
        pass

    def test_upload_samples_as_version(self):
        """url(r'^ajax/upload_samples_as_version/$', 'workshop.views.ajax_upload_samples_as_version', name="workbench.ajax_upload_samples_as_version"),"""
        pass
        
    def test_rename_project(self):
        """url(r'^ajax/rename_project/$', 'workshop.views.ajax_rename_project', name="workbench.ajax_rename_project"),"""
        pass

    def test_dependency_ownership(self):
        """url(r'^ajax/dependency_ownership/$', 'workshop.views.ajax_dependency_ownership', name="workbench.ajax_dependency_ownership"),"""
        pass

    def test_provide_project(self):
        """url(r'^ajax/provide_project/$', 'workshop.views.ajax_provide_project', name="workbench.ajax_provide_project"),"""
        pass

    def test_provide_mp3(self):
        """url(r'^ajax/provide_mp3/$', 'workshop.views.ajax_provide_mp3', name="workbench.ajax_provide_mp3"),"""
        pass

    def test_checkout(self):
        """url(r'^ajax/checkout/$', 'workshop.views.ajax_checkout', name="workbench.ajax_checkout"),"""
        pass

    def test_checkin(self):
        """url(r'^ajax/checkin/$', 'workshop.views.ajax_checkin', name="workbench.ajax_checkin"),"""
        pass

    def test_create(self):
        """url(r'^create/$', 'workshop.views.create_band', name="workbench.create_band"),"""
        pass

    def test_band(self):
        """url(r'^band/(\d+)/$', 'workshop.views.band', name="workbench.band"),"""
        pass

    def test_band_settings_space(self):
        """url(r'^band/(\d+)/settings/$', 'workshop.views.band_settings', name="workbench.band_settings"),"""
        pass

    def test_band_settings_space(self):
        """url(r'^band/(\d+)/settings/space/$', 'workshop.views.band_settings_space', name="workbench.band_settings_space"),"""
        pass

    def test_create_project(self):
        """url(r'^band/(\d+)/create/$', 'workshop.views.create_project', name="workbench.create_project"),"""
        pass

    def test_project(self):
        """url(r'^band/(\d+)/project/(\d+)/$', 'workshop.views.project', name="workbench.project"),"""
        pass

    def test_band_invite(self):
        """url(r'^band/(\d+)/invite/$', 'workshop.views.band_invite', name="workbench.band_invite"),"""
        pass

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
        """url(r'^plugin/(.+)/$', 'workshop.views.plugin', name="workbench.plugin"),"""
        pass

    def test_studio(self):
        """url(r'^studio/(.+)/$', 'workshop.views.studio', name="workbench.studio"),"""
        pass

