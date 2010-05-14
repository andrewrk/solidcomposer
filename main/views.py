from django.core.mail import send_mail
from django.template import RequestContext, Context, Template
from django.template.loader import get_template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404

from opensourcemusic.main.forms import *
from opensourcemusic import settings

import simplejson as json
from datetime import datetime, timedelta
import string
import random

def json_response(data):
    return HttpResponse(json_dump(data), mimetype="text/plain")

def remove_unsafe_keys(hash, model):
    """
    look for UNSAFE_KEYS in the model. if it exists, delete all those entries
    from the hash.
    """
    if issubclass(model, User):
        check = (
            'password',
            'user_permissions',
            'is_user',
            'is_staff'
            'is_superuser',
            'email',
            'first_name',
            'last_name',
            'groups',
        )
    else:
        try:
            check = model.UNSAFE_KEYS
        except AttributeError:
            return

    for key in check:
        if hash.has_key(key):
            del hash[key]
        
def safe_model_to_dict(model_instance):
    hash = model_to_dict(model_instance)
    remove_unsafe_keys(hash, type(model_instance))
    if issubclass(type(model_instance), User):
        hash['get_profile'] = safe_model_to_dict(model_instance.get_profile())
    return hash

def json_dthandler(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%B %d, %Y %H:%M:%S')
    else:
        return None

def json_dump(obj):
    return json.dumps(obj, default=json_dthandler)
    
def activeUser(request):
    """
    touch the request's user if they are authenticated in order
    to update the last_activity field
    """
    if request.user.is_authenticated():
        request.user.get_profile().save() # set active date

def ajax_login_state(request):
    activeUser(request)

    # build the object
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
    }

    if request.user.is_authenticated():
        data['user'].update(safe_model_to_dict(request.user))
        data['user']['get_profile']['get_points'] = request.user.get_profile().get_points()

    return json_response(data)

def user_logout(request):
    logout(request)
    return HttpResponseRedirect(request.GET.get('next', '/'))

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
                    err_msg = 'Your account is not activated.'
            else:
                err_msg = 'Invalid login.'
    else:
        form = LoginForm(initial={'next_url': request.GET.get('next', '/')})
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
                err_msg = 'Your account is not activated.'
        else:
            err_msg = 'Invalid login.'
    else:
        err_msg = 'No login data supplied.'

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
            band.save()

            # create a profile
            profile = Profile()
            profile.user = user
            profile.solo_band = band
            profile.activated = False
            profile.activate_code = create_hash(32)
            profile.logon_count = 0
            profile.save()

            # send an activation email
            subject = "Account Confirmation - SolidComposer"
            message = get_template('activation_email.txt').render(Context({ 'username': user.username, 'code': profile.activate_code}))
            from_email = 'admin@solidcomposer.com'
            to_email = user.email
            send_mail(subject, message, from_email, [to_email], fail_silently=True)

            return HttpResponseRedirect("/register/pending/")
    else:
        form = RegisterForm()
    return render_to_response('register.html', {'form': form}, context_instance=RequestContext(request))

def create_hash(length):
    """
    returns a string of length length with random alphanumeric characters
    """
    chars = string.letters + string.digits
    code = ""
    for i in range(length):
        code += chars[random.randint(0, len(chars)-1)]
    return code

def confirm(request, username, code):
    try:
        user = User.objects.get(username=username)
    except:
        err_msg = "Invalid username. Your account may have expired. You can try registering again."
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
        err_msg = "Invalid activation code. Nice try!"
        return render_to_response('confirm_failure.html', locals(), context_instance=RequestContext(request))

def userpage(request, username):
    """
    TODO
    """
    pass
