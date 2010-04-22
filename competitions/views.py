from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict

from opensourcemusic.competitions.models import *
from opensourcemusic.settings import MEDIA_URL, MEDIA_ROOT
from opensourcemusic.main.views import activeUser

from datetime import datetime
import simplejson as json

def ajax_available(request):
    activeUser(request)

    # query the db
    now = datetime.now()

    upcoming = Competition.objects.filter(start_date__gt=now).order_by('start_date')
    ongoing = Competition.objects.filter(start_date__lte=now).filter(vote_deadline__gt=now).order_by('start_date')
    closed = Competition.objects.filter(vote_deadline__lte=now).order_by('start_date')

    # don't show bookmarked items
    if request.user.is_authenticated():
        upcoming.exclude(players_bookmarked__in=request.user.get_profile())
        ongoing.exclude(players_bookmarked__in=request.user.get_profile())
        closed.exclude(players_bookmarked__in=request.user.get_profile())

    # build the json object
    data = {
        'upcoming': [model_to_dict(x) for x in upcoming],
        'ongoing': [model_to_dict(x) for x in ongoing],
        'closed': [model_to_dict(x) for x in closed],
    }

    return HttpResponse(json.dumps(data), mimetype="text/plain")

def ajax_owned(request):
    activeUser()
    pass
