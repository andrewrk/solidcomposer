from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict

from opensourcemusic.competitions.models import *
from opensourcemusic.settings import MEDIA_URL, MEDIA_ROOT
from opensourcemusic.main.views import activeUser, safe_model_to_dict, json_dump

from datetime import datetime

def ajax_available(request):
    activeUser(request)

    upcoming = filter_upcoming(Competition.objects)
    ongoing = filter_ongoing(Competition.objects)
    closed = filter_closed(Competition.objects)

    # don't show bookmarked items
    if request.user.is_authenticated():
        pkeys = request.user.get_profile().competitions_bookmarked.values_list('pk')
        upcoming.exclude(pk__in=pkeys)
        ongoing.exclude(pk__in=pkeys)
        closed.exclude(pk__in=pkeys)

    # build the json object
    data = {
        'upcoming': [safe_model_to_dict(x) for x in upcoming],
        'ongoing': [safe_model_to_dict(x) for x in ongoing],
        'closed': [safe_model_to_dict(x) for x in closed],
    }

    return HttpResponse(json_dump(data), mimetype="text/plain")

def filter_upcoming(query_set):
    now = datetime.now()
    return query_set.filter(start_date__gt=now).order_by('start_date')

def filter_ongoing(query_set):
    now = datetime.now()
    return query_set.filter(start_date__lte=now).filter(vote_deadline__gt=now).order_by('start_date')

def filter_closed(query_set):
    now = datetime.now()
    return query_set.filter(vote_deadline__lte=now).order_by('start_date')

def ajax_owned(request):
    activeUser(request)

    # only show bookmarked items
    now = datetime.now()
    bookmarked = request.user.get_profile().competition_set

    upcoming = filter_upcoming(bookmarked)
    ongoing = filter_ongoing(bookmarked)
    closed = filter_closed(bookmarked)

    # build the json object
    data = {
        'upcoming': [safe_model_to_dict(x) for x in upcoming],
        'ongoing': [safe_model_to_dict(x) for x in ongoing],
        'closed': [safe_model_to_dict(x) for x in closed],
    }

    return HttpResponse(json_dump(data), mimetype="text/plain")
