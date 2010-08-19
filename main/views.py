from django.db.models import Q
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context
from django.template.loader import get_template
from main import design, payment
from main.common import json_response, json_login_required, json_post_required, \
    get_obj_from_request, json_failure, json_success, create_hash, \
    send_html_mail, json_dump
from main.forms import LoginForm, RegisterForm, ContactForm, \
    ChangePasswordForm, EmailSubscriptionsForm, PasswordResetForm
from main.models import SongCommentNode, Band, Profile, BandMember, Song, \
    AccountPlan
from workshop.models import LogEntry

from datetime import datetime, timedelta

def ajax_login_state(request):
    user = request.user

    # build the object
    data = {
        'user': {
            'is_authenticated': user.is_authenticated(),
        },
    }

    if user.is_authenticated():
        data['user'].update(user.get_profile().to_dict())

    return json_response(data)

def user_logout(request):
    logout(request)

    home_url = reverse('home')
    return HttpResponseRedirect(request.GET.get('next', home_url))

def user_login(request):
    err_msg = ''
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                if user.is_active and user.get_profile().activated:
                    login(request, user)
                    return HttpResponseRedirect(form.cleaned_data.get('next_url'))
                else:
                    err_msg = design.your_account_not_activated
            else:
                err_msg = design.invalid_login
    else:
        home_url = reverse('home')
        form = LoginForm(initial={'next_url': request.GET.get('next', home_url)})
    return render_to_response('login.html', {'form': form, 'err_msg': err_msg }, context_instance=RequestContext(request))

def ajax_login(request):
    err_msg = ''
    success = False
    if request.method == 'POST':
        user = authenticate(username=request.POST.get('username', ''), password=request.POST.get('password', ''))
        if user is not None:
            if user.is_active and user.get_profile().activated:
                login(request, user)
                success = True
            else:
                err_msg = design.your_account_not_activated
        else:
            err_msg = design.invalid_login
    else:
        err_msg = design.no_login_data_supplied

    data = {
        'success': success,
        'err_msg': err_msg,
    }

    return json_response(data)

def ajax_logout(request):
    logout(request)

    data = {
        'success': True,
    }

    return json_response(data)

@json_login_required
@json_post_required
def ajax_comment(request):
    parent = get_obj_from_request(request.POST, 'parent', SongCommentNode)

    if parent is None:
        return json_failure(design.bad_song_comment_node_id)

    # make sure the user has permission to critique
    if not parent.song.permission_to_critique(request.user):
        return json_failure(design.you_dont_have_permission_to_comment)

    # make sure the parent has enabled replies
    if parent.reply_disabled:
        return json_failure(design.comments_disabled_for_this_version)

    position = request.POST.get('position')
    if position is not None:
        try:
            position = float(position)
        except ValueError:
            position = None

        if position < 0 or position > parent.song.length:
            return json_failure(design.invalid_position)

    content = request.POST.get('content')

    if len(content) == 0 or len(content) > 2000:
        return json_failure(design.content_wrong_length)

    node = SongCommentNode()
    node.song = parent.song
    node.parent = parent
    node.owner = request.user
    node.content = content
    node.position = position
    node.reply_disabled = False
    node.save()

    return json_success(node.to_dict())

@json_login_required
@json_post_required
def ajax_delete_comment(request):
    node = get_obj_from_request(request.POST, 'comment', SongCommentNode)

    if node is None:
        return json_failure(design.bad_song_comment_node_id)

    # can only delete own comments
    if node.owner != request.user:
        return json_failure(design.can_only_delete_your_own_comment)

    # can only delete within a certain amount of time
    now = datetime.now()
    if now > node.date_created + timedelta(hours=settings.COMMENT_EDIT_TIME_HOURS):
        return json_failure(design.too_late_to_delete_comment)

    node.delete()
    return json_success()

@json_login_required
@json_post_required
def ajax_edit_comment(request):
    node = get_obj_from_request(request.POST, 'comment', SongCommentNode)

    if node is None:
        return json_failure(design.bad_song_comment_node_id)

    # can only edit own comments
    if node.owner != request.user:
        return json_failure(design.can_only_edit_your_own_comment)

    # can only delete within a certain amount of time
    now = datetime.now()
    if now > node.date_created + timedelta(hours=settings.COMMENT_EDIT_TIME_HOURS):
        return json_failure(design.too_late_to_edit_comment)

    content = request.POST.get('content', '')
    
    if len(content) == 0 or len(content) > 2000:
        return json_failure(design.content_wrong_length)

    node.content = content
    node.save()

    return json_success(node.to_dict())

def user_register_plan(request, plan_url):
    "plan_url of 'free' means free plan"
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                plan_id = int(form.cleaned_data.get('plan'))
                plan = AccountPlan.objects.get(pk=plan_id)
            except AccountPlan.DoesNotExist:
                plan_id = 0
                plan = None

            # create the user
            user = User.objects.create_user(form.cleaned_data.get('username'),
                form.cleaned_data.get('email'),
                form.cleaned_data.get('password'))
            user.save()

            # create a band
            band = Band()
            band.title = form.cleaned_data.get('artist_name')
            band.total_space = settings.BAND_INIT_SPACE
            band.save()

            # create a profile
            profile = Profile()
            profile.user = user
            profile.solo_band = band
            profile.activated = False
            profile.activate_code = create_hash(32)
            profile.logon_count = 0
            profile.band_count_limit = settings.FREE_BAND_LIMIT
            profile.save()

            # make them a manager
            manager = BandMember()
            manager.user = user
            manager.band = band
            manager.role = BandMember.MANAGER
            manager.save()

            # send an activation email
            subject = design.account_confirmation
            context = Context({
                'user': user.username,
                'activate_url': request.build_absolute_uri(reverse('confirm', args=[user.username, profile.activate_code])),
                'host': request.get_host(),
            })
            message_txt = get_template('email/activation.txt').render(context)
            message_html = get_template('email/activation.html').render(context)
            send_html_mail(subject, message_txt, message_html, [user.email])

            if plan is None:
                return HttpResponseRedirect(reverse("register_pending"))
            else:
                return HttpResponseRedirect(payment.pipeline_url(user, request.build_absolute_uri(reverse("register_pending")), plan))
    else:
        try:
            plan = AccountPlan.objects.get(url=plan_url)
            plan_id = plan.id
        except AccountPlan.DoesNotExist:
            plan = None
            plan_id = 0

        form = RegisterForm(initial={'plan': plan_id})
    return render_to_response('register.html', {'form': form}, context_instance=RequestContext(request))

def user_register(request):
    return user_register_plan(request, 0)

def register_pending(request):
    status, transaction = payment.process_pipeline_result(request)
    payment_result = {
        'SUCCESS': payment.SUCCESS,
        'FAILURE': payment.FAILURE,
        'NO_PIPELINE': payment.NO_PIPELINE,
        'INVALID_SIGNATURE': payment.INVALID_SIGNATURE,
    }
    if status == payment.SUCCESS:
        # give the user the premium account
        profile = transaction.user.get_profile()
        plan = transaction.plan
        profile.plan = plan
        profile.band_count_limit = plan.band_count_limit
        profile.purchased_bytes = plan.total_space
        profile.usd_per_month = plan.usd_per_month
        # give them a day while payment cron job runs
        profile.account_expire_date = datetime.now()
        profile.active_transaction = transaction
        profile.save()

    return render_to_response('pending.html', locals(), context_instance=RequestContext(request))

def confirm(request, username, code):
    try:
        user = User.objects.get(username=username)
    except:
        err_msg = design.invalid_username_tips
        return render_to_response('confirm_failure.html', locals(), context_instance=RequestContext(request))

    profile = user.get_profile()
    real_code = profile.activate_code

    if real_code == code:
        # activate the account
        user.is_active = True
        user.save()
        profile.activated = True
        profile.save()
        user = request.user
        profile = None
        return render_to_response('confirm_success.html', locals(), context_instance=RequestContext(request))
    else:
        err_msg = design.invalid_activation_code
        user = request.user
        return render_to_response('confirm_failure.html', locals(), context_instance=RequestContext(request))

def userpage(request, username):
    user = get_object_or_404(User, username=username)
    members = BandMember.objects.filter(user=user).order_by('-space_donated')
    songs = Song.objects.filter(Q(owner=user), Q(is_open_for_comments=True)|Q(is_open_source=True)).order_by('-date_added')[:10]
    song_data = json_dump([song.to_dict(chains=['band', 'comment_node']) for song in songs])
    if request.user.is_authenticated():
        user_data = json_dump(request.user.get_profile().to_dict())
    else:
        user_data = 'null'
    return render_to_response('userpage.html', locals(), context_instance=RequestContext(request))

def bandpage(request, band_url):
    band = get_object_or_404(Band, url=band_url)
    songs = Song.objects.filter(Q(band=band), Q(is_open_for_comments=True)|Q(is_open_source=True)).order_by('-date_added')[:10]
    song_data = json_dump([song.to_dict(chains=['band', 'comment_node']) for song in songs])
    user_data = json_dump(request.user.get_profile().to_dict())
    return render_to_response('bandpage.html', locals(), context_instance=RequestContext(request))

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # email myself
            customer_email = form.cleaned_data.get('from_email')
            content = form.cleaned_data.get('message')
            to_email = 'support@solidcomposer.com'
            from_email = 'support@solidcomposer.com'
            subject = "SolidComposer Contact Message from {0}".format(customer_email)
            message = get_template('contact_message.txt').render(Context({'email': customer_email, 'content': content}))
            msg = EmailMessage(subject, message, from_email, [to_email], headers={'Reply-To': customer_email})
            msg.send(fail_silently=True)

            return HttpResponseRedirect(reverse("contact_thanks"))
    else:
        form = ContactForm()

    return render_to_response('contact.html', locals(), context_instance=RequestContext(request))

@login_required
def account_plan(request):
    """The page that shows the user what plan their on and wants them to click to the upgrade plans page."""

    err_msg = ""
    if request.method == 'POST':
        changes = []
        space_total = 0
        for key, val in request.POST.iteritems():
            # format: member-X-amt=Y
            # X = member id, Y = amount donated
            member_str, member_id, amt_str = key.split('-')
            if member_str != 'member' or amt_str != 'amt':
                err_msg = design.invalid_parameters
                break
            try:
                member_id = int(member_id)
                member = BandMember.objects.get(pk=member_id)
            except ValueError, BandMember.DoesNotExist:
                err_msg = design.bad_band_member_id
                break

            # make sure the user is the band member
            if member.user != request.user:
                err_msg = design.can_only_edit_your_own_amount_donated
                break

            try:
                val = int(val)
            except ValueError:
                err_msg = design.invalid_amount
                break

            changes.append((member, val,))
            space_total += val

        if err_msg == "":
            if space_total <= request.user.get_profile().purchased_bytes:
                # everything is good. apply the change.
                # also create log entries for affected bands
                for member, new_space in changes:
                    old_space = member.space_donated
                    if old_space != new_space:
                        # save new space into member
                        member.space_donated = new_space
                        member.save()

                        # add or take away space from the band
                        band = member.band
                        band.total_space += new_space - old_space
                        band.save()

                        # make log entry
                        entry = LogEntry()
                        entry.entry_type = LogEntry.SPACE_ALLOCATED_CHANGE
                        entry.band = member.band
                        entry.catalyst = request.user
                        entry.old_amount = old_space
                        entry.new_amount = new_space
                        entry.save()

                return HttpResponseRedirect(reverse('account.plan'))
            else:
                err_msg = design.you_dont_have_enough_space_to_do_that

    user = request.user
    plan = user.get_profile().plan
    if plan is None:
        plan = {
            'title': 'Free',
            'band_count_limit': settings.FREE_BAND_LIMIT,
            'usd_per_month': 0,
            'total_space': 0,
        }
    memberships = BandMember.objects.filter(user=user).order_by('-space_donated')
    return render_to_response('account/plan.html', locals(), context_instance=RequestContext(request))

@login_required
def account_email(request):
    user = request.user
    profile = user.get_profile()
    if request.method == 'POST':
        form = EmailSubscriptionsForm(request.POST)
        if form.is_valid():
            profile.email_notifications = form.cleaned_data.get('notifications')
            profile.email_newsletter = form.cleaned_data.get('newsletter')
            profile.save()
            success = True
    else:
        form = EmailSubscriptionsForm(initial={
            'notifications': user.get_profile().email_notifications,
            'newsletter': user.get_profile().email_newsletter,
        })
    return render_to_response('account/email.html', locals(), context_instance=RequestContext(request))

@login_required
def account_password(request):
    user = request.user
    err_msg = ''
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data.get('old_password')
            if user.check_password(old_password):
                user.set_password(form.cleaned_data.get('new_password'))
                user.save()
                return HttpResponseRedirect(reverse('account.password.ok'))
            else:
                err_msg = design.invalid_old_password
    else:
        form = ChangePasswordForm()

    return render_to_response('account/password.html', locals(), context_instance=RequestContext(request))

def account_password_reset(request):
    err_msg = ''
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                err_msg = design.no_such_email_in_database

            if err_msg == '':
                # change password to new random hash
                new_password = create_hash(12)

                # save it
                user.set_password(new_password)
                user.save()

                # send it in email
                subject = design.password_reset_on_website
                context = Context({
                    'new_password': new_password,
                    'host': request.get_host(),
                })
                message_txt = get_template('email/password_reset.txt').render(context)
                message_html = get_template('email/password_reset.html').render(context)
                send_html_mail(subject, message_txt, message_html, [email])

                return HttpResponseRedirect(reverse('account.password.reset.ok'))
    else:
        form = PasswordResetForm()

    return render_to_response('account/password_reset.html', locals(), context_instance=RequestContext(request))

def plans(request):
    """The page where we try to get people to sign up for paying us money"""
    user = request.user
    free_plan = {
        'title': 'Free',
        'usd_per_month': 0,
        'total_space': 0,
        'band_count_limit': settings.FREE_BAND_LIMIT,
    }
    plans = AccountPlan.objects.order_by('usd_per_month')
    return render_to_response('plans.html', locals(), context_instance=RequestContext(request))

def home(request):
    """If they're logged in, do the same thing as dashboard. If not, do the same thing as landing."""
    if request.user.is_authenticated():
        return dashboard(request)
    else:
        return landing(request)

@login_required
def dashboard(request):
    return render_to_response('dashboard.html', {}, context_instance=RequestContext(request))

def landing(request):
    return render_to_response('landing.html', {}, context_instance=RequestContext(request))
