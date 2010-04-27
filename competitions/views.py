from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404

from opensourcemusic.competitions.models import *
from opensourcemusic.settings import MEDIA_URL, MEDIA_ROOT
from opensourcemusic.main.views import activeUser, safe_model_to_dict, json_dump
from opensourcemusic.competitions.forms import *

from datetime import datetime

def ajax_unbookmark(request, id):
    data = {'success': False}
    if request.user.is_authenticated():
        comp = get_object_or_404(Competition, id=int(id))
        prof = request.user.get_profile()
        prof.competitions_bookmarked.remove(comp)
        prof.save()
        data['success'] = True

    return HttpResponse(json_dump(data), mimetype="text/plain")

def ajax_bookmark(request, id):
    data = {'success': False}
    if request.user.is_authenticated():
        comp = get_object_or_404(Competition, id=int(id))
        prof = request.user.get_profile()
        prof.competitions_bookmarked.add(comp)
        prof.save()
        data['success'] = True

    return HttpResponse(json_dump(data), mimetype="text/plain")

def ajax_available(request):
    upcoming = filter_upcoming(Competition.objects)
    ongoing = filter_ongoing(Competition.objects)
    closed = filter_closed(Competition.objects)

    # don't show bookmarked items
    if request.user.is_authenticated():
        pkeys = request.user.get_profile().competitions_bookmarked.values_list('pk')
        upcoming = upcoming.exclude(pk__in=pkeys)
        ongoing = ongoing.exclude(pk__in=pkeys)
        closed = closed.exclude(pk__in=pkeys)

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
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
    }

    if not request.user.is_authenticated():
        return HttpResponse(json_dump(data), mimetype="text/plain")

    # only show bookmarked items
    now = datetime.now()
    bookmarked = request.user.get_profile().competitions_bookmarked

    upcoming = filter_upcoming(bookmarked)
    ongoing = filter_ongoing(bookmarked)
    closed = filter_closed(bookmarked)

    # build the json object
    data.update({
        'upcoming': [safe_model_to_dict(x) for x in upcoming],
        'ongoing': [safe_model_to_dict(x) for x in ongoing],
        'closed': [safe_model_to_dict(x) for x in closed],
    })

    return HttpResponse(json_dump(data), mimetype="text/plain")

@login_required
def create(request):
    err_msg = ""
    if request.method == 'POST':
        form = CreateCompetitionForm(request.POST)
        if form.is_valid() and request.user.is_authenticated():
            # create and save the Competition
            comp = Competition()
            comp.title = form.cleaned_data.get('title')
            comp.host = request.user.get_profile()

            comp.preview_theme = form.cleaned_data.get('preview_theme', False)
            if form.cleaned_data.get('have_theme', False):
                comp.theme = form.cleaned_data.get('theme', '')

            comp.preview_rules = form.cleaned_data.get('preview_rules', False)
            if form.cleaned_data.get('have_rules', False):
                comp.rules = form.cleaned_data.get('rules', '')

            comp.have_listening_party = form.cleaned_data.get('have_listening_party', True)
            if comp.have_listening_party:
                comp.listening_party_start_date = form.cleaned_data.get('listening_party_date')

            comp.start_date = form.cleaned_data.get('start_date')
            comp.submit_deadline = form.cleaned_data.get('submission_deadline_date')
            # calculate vote deadline 
            quantity = int(form.cleaned_data.get('vote_time_quantity'))
            quantifier = int(form.cleaned_data.get('vote_time_measurement'))

            multiplier = {
                HOURS: 60*60,
                DAYS: 24*60*60,
                WEEKS: 7*24*60*60,
            }
            
            comp.vote_period_length = quantity * multiplier[quantifier]

            comp.save()

            return HttpResponseRedirect('/arena/')
    else:
        form = CreateCompetitionForm()
    
    return render_to_response('arena/create.html', locals(), context_instance=RequestContext(request))

def competition(request, id):
    competition = get_object_or_404(Competition, id=int(id))
    return render_to_response('arena/competition.html', locals(), context_instance=RequestContext(request))

