from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.template import RequestContext, Context, Template
from django.template.loader import get_template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response, get_object_or_404

from main.models import *
from main.forms import *
from main.common import *
from main import design
from django.conf import settings

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
    parent_id_str = request.POST.get('parent', 0)
    try:
        parent_id = int(parent_id_str)
    except ValueError:
        parent_id = 0
    try:
        parent = SongCommentNode.objects.get(pk=parent_id)
    except SongCommentNode.DoesNotExist:
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

    if not content:
        return json_failure(design.content_required)

    node = SongCommentNode()
    node.song = parent.song
    node.parent = parent
    node.owner = request.user
    node.content = content
    node.position = position
    node.reply_disabled = False
    node.save()

    return json_success(node.to_dict())

def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
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
            subject = "Account Confirmation - SolidComposer"
            message = get_template('activation_email.txt').render(Context({ 'username': user.username, 'code': profile.activate_code}))
            from_email = 'admin@solidcomposer.com'
            to_email = user.email
            send_mail(subject, message, from_email, [to_email], fail_silently=True)

            return HttpResponseRedirect(reverse("register_pending"))
    else:
        form = RegisterForm()
    return render_to_response('register.html', {'form': form}, context_instance=RequestContext(request))

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
        return render_to_response('confirm_success.html', locals(), context_instance=RequestContext(request))
    else:
        err_msg = design.invalid_activation_code
        return render_to_response('confirm_failure.html', locals(), context_instance=RequestContext(request))

def userpage(request, username):
    """
    TODO
    """
    return render_to_response('userpage.html', locals(), context_instance=RequestContext(request))
