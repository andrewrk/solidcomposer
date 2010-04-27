from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict
from opensourcemusic.main.forms import *

from opensourcemusic.settings import MEDIA_URL, MEDIA_ROOT

import simplejson as json
import datetime

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
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
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
