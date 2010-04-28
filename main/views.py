from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404

from opensourcemusic.main.forms import *
from opensourcemusic.settings import MEDIA_URL, MEDIA_ROOT

import simplejson as json
from datetime import datetime

def remove_unsafe_keys(hash, model):
    """
    look for UNSAFE_KEYS in the model. if it exists, delete all those entries
    from the hash.
    """
    if isinstance(model, User):
        check = (
            'password',
            'user_permissions',
            'is_user',
            'is_staff'
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
        data['user']['get_profile'] = safe_model_to_dict(request.user.get_profile())
        data['user']['get_profile']['get_points'] = request.user.get_profile().get_points()

    return HttpResponse(json_dump(data), mimetype="text/plain")

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

    return HttpResponse(json_dump(data), mimetype="text/plain")

def ajax_logout(request):
    logout(request)

    data = {
        'success': True,
    }

    return HttpResponse(json_dump(data), mimetype="text/plain")

def python_date(js_date):
    """
    convert a javascript date to a python date
    format: Wed Apr 28 2010 04:20:43 GMT-0700 (MST)
    """
    return datetime.strptime(js_date[:24], "%a %b %d %Y %H:%M:%S")

def user_can_chat(room, user):
    if room.permission_type == OPEN:
        return True
    else:
        # user has to be signed in
        if not user.is_authenticated():
            return False

        if room.permission_type == WHITELIST:
            # user has to be on the whitelist
            if room.whitelist.filter(pk=user.get_profile().id).count() != 1:
                return False
        elif room.permission_type == BLACKLIST:
            # user is blocked if he is on the blacklist 
            if room.blacklist.filter(pk=user.get_profile().id).count() == 1:
                return False

        return True

def ajax_chat(request):
    latest_check = request.GET.get('latest_check', 'null')
    room_id = request.GET.get('room', 0)
    try:
        room_id = int(room_id)
    except:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    # make sure user has permission to be in this room
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'has_permission': False,
        },
    }

    if request.user.is_authenticated():
        data['user']['get_profile'] = safe_model_to_dict(request.user.get_profile())
        data['user']['username'] = request.user.username

    data['user']['has_permission'] = user_can_chat(room, request.user)

    def add_to_message(msg):
        d = safe_model_to_dict(msg)
        d['author'] = safe_model_to_dict(msg.author)
        d['author']['username'] = msg.author.user.username
        return d

    if latest_check == 'null':
        # get entire log for this chat.
        data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room).order_by('timestamp')]
    else:
        check_date = python_date(latest_check)
        data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room, timestamp__gt=check_date).order_by('timestamp')]

    return HttpResponse(json_dump(data), mimetype="text/plain")

def ajax_say(request):
    room_id = request.POST.get('room', 0)
    try:
        room_id = int(room_id)
    except:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'has_permission': False,
        },
    }

    message = request.POST.get('message', '')

    if message == "" or not request.user.is_authenticated():
        return HttpResponse(json_dump(data), mimetype="text/plain")

    data['user']['has_permission'] = user_can_chat(room, request.user)
    if not data['user']['has_permission']:
        return HttpResponse(json_dump(data), mimetype="text/plain")

    # we're clear. add the message
    m = ChatMessage()
    m.room = room
    m.type = MESSAGE
    m.author = request.user.get_profile()
    m.message = message
    m.save()

    return HttpResponse(json_dump(data), mimetype="text/plain")
