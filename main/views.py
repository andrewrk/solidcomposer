from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict

from opensourcemusic.settings import MEDIA_URL, MEDIA_ROOT

import simplejson as json

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
        data['user'].update(model_to_dict(request.user))
        data['user']['get_profile'] = model_to_dict(request.user.get_profile())

    return HttpResponse(json.dumps(data), mimetype="text/plain")

def ajax_login(request):
    
    pass

def ajax_logout(request):
    pass
