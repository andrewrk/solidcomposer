from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Count

from main.common import safe_model_to_dict, json_response, json_login_required
from main.models import *
from competitions.models import *
from competitions.forms import *
from competitions import design
from chat.models import *
import settings

from datetime import datetime, timedelta

from main.uploadsong import upload_song

def ajax_submit_entry(request):
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
        'success': False,
        'reason': '',
    }
    if not request.user.is_authenticated():
        data['reason'] = design.not_authenticated
        return json_response(data)

    if request.method != 'POST':
        data['reason'] = design.must_submit_via_post
        return json_response(data)

    compo_id = request.POST.get('compo', 0)
    try:
        compo_id = int(compo_id)
    except ValueError:
        compo_id = 0
    
    try:
        compo = Competition.objects.get(pk=compo_id)
    except Competition.DoesNotExist:
        data['reason'] = design.competition_not_found
        return json_response(data)

    # make sure it's still submission time
    now = datetime.now()
    if now >= compo.submit_deadline:
        data['reason'] = design.past_submission_deadline
        return json_response(data)

    if now <= compo.start_date:
        data['reason'] = design.competition_not_started
        return json_response(data)

    title = request.POST.get('entry-title','')
    comments = request.POST.get('entry-comments', '')
    mp3_file = request.FILES.get('entry-file-mp3')
    source_file = request.FILES.get('entry-file-source')

    # make sure files are small enough
    if mp3_file is None:
        data['reason'] = design.mp3_required
        return json_response(data)

    if mp3_file.size > settings.FILE_UPLOAD_SIZE_CAP:
        data['reason'] = design.mp3_too_big
        return json_response(data)

    if not source_file is None:
        if source_file.size > settings.FILE_UPLOAD_SIZE_CAP:
            data['reason'] = design.source_file_too_big
            return json_response(data)

    if title == '':
        data['reason'] = design.entry_title_required
        return json_response(data)

    result = upload_song(request.user,
        file_mp3_handle=mp3_file,
        file_source_handle=source_file, 
        max_song_len=settings.COMPO_ENTRY_MAX_LEN,
        band=request.user.get_profile().solo_band,
        song_title=title,
        song_album=compo.title)

    if not result['success']:
        data['reason'] = result['reason']
        return json_response(data)

    song = result['song']

    entries = Entry.objects.filter(owner=request.user, competition=compo)
    if entries.count() > 0:
        # resubmitting. edit old entry and song
        entry = entries[0]
        old_length = entry.song.length
        buffer_time = 0
        entry.song.delete()
    else:
        # create new entry
        entry = Entry()
        old_length = 0
        buffer_time = settings.LISTENING_PARTY_BUFFER_TIME

    song.comments = comments
    song.save()

    entry.competition = compo
    entry.owner = request.user
    entry.song = song
    entry.save()

    # update competition dates based on this newfound length 
    vote_period_delta = timedelta(seconds=compo.vote_period_length)
    if compo.have_listening_party:
        compo.listening_party_end_date += timedelta(seconds=(song.length-old_length+buffer_time))
        compo.vote_deadline = compo.listening_party_end_date + vote_period_delta
    else:
        compo.vote_deadline = compo.submit_deadline + vote_period_delta
    compo.save()

    chatroom = compo.chat_room
    chatroom.end_date = compo.listening_party_end_date + timedelta(hours=1)
    chatroom.save()

    data['success'] = True
    del data['reason']

    return json_response(data)

def max_vote_count(entry_count):
    """
    given how many entrants there are, compute how many votes each person gets.
    """
    x = int(entry_count / 3)
    if x < 1:
        x = 1

    return x

def ajax_compo(request, id):
    id = int(id)
    compo = get_object_or_404(Competition, id=id)

    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
        'compo': compo_to_dict(compo, request.user),
        'party': {
            'buffer_time': settings.LISTENING_PARTY_BUFFER_TIME,
        }
    }

    # entries. if competition is closed, sort by vote count.
    now = datetime.now()
    compo_closed = compo.isClosed()
    def add_to_entry(entry):
        d = safe_model_to_dict(entry)
        d['submit_date'] = entry.submit_date
        d['edit_date'] = entry.edit_date
        d['owner'] = safe_model_to_dict(entry.owner)
        d['owner']['solo_band'] = safe_model_to_dict(entry.owner.get_profile().solo_band)
        d['song'] = safe_model_to_dict(entry.song)
        d['song']['band'] = safe_model_to_dict(entry.song.band)
        if compo_closed:
            d['vote_count'] = ThumbsUp.objects.filter(entry=entry).count()
        return d

    data['entries'] = [add_to_entry(x) for x in compo.entry_set.all()]

    if request.user.is_authenticated():
        max_votes = max_vote_count(compo.entry_set.count())
        used_votes = ThumbsUp.objects.filter(owner=request.user, entry__competition=compo)

        data['user'].update(safe_model_to_dict(request.user))
        data['votes'] = {
            'max': max_votes,
            'used': [safe_model_to_dict(x) for x in used_votes],
            'left': max_votes - used_votes.count(),
        }
        user_entries = Entry.objects.filter(competition=compo, owner=request.user)
        data['submitted'] = (user_entries.count() > 0)
        if user_entries.count() > 0:
            data['user_entry'] = safe_model_to_dict(user_entries[0].song)

    return json_response(data)

@json_login_required
def ajax_unbookmark(request, id):
    id = int(id)
    comp = get_object_or_404(Competition, id=id)
    prof = request.user.get_profile()
    prof.competitions_bookmarked.remove(comp)
    prof.save()
    data = {'success': True}
    return json_response(data)

@json_login_required
def ajax_bookmark(request, id):
    comp = get_object_or_404(Competition, id=int(id))
    prof = request.user.get_profile()
    prof.competitions_bookmarked.add(comp)
    prof.save()
    data = {'success': True}
    return json_response(data)

def compo_to_dict(compo, user):
    data = safe_model_to_dict(compo)

    data['have_theme'] = compo.theme != ''
    data['have_rules'] = compo.rules != ''

    if compo.rulesVisible():
        data['rules'] = compo.rules
    if compo.themeVisible():
        data['theme'] = compo.theme

    if user.is_authenticated():
        # see if the user entered the compo
        entries = Entry.objects.filter(owner=user, competition=compo)
        if entries.count() > 0:
            data['user_entered'] = True
            entry = entries[0]
            data['vote_count'] = ThumbsUp.objects.filter(entry=entry).count()
    return data

def compoRequest(request, compos):
    page_str = request.GET.get('page', 1) 
    try:
        page_number = int(page_str)
    except ValueError:
        page_number = 1

    paginator = Paginator(compos, settings.ITEMS_PER_PAGE)

    # build the json object
    data = {
        'compos': [compo_to_dict(x, request.user) for x in paginator.page(page_number).object_list],
        'page_count': paginator.num_pages,
        'page_number': page_number,
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
    }

    return json_response(data)

def ajax_available(request):
    compos = Competition.objects

    # don't show bookmarked items
    if request.user.is_authenticated():
        pkeys = request.user.get_profile().competitions_bookmarked.values_list('pk')
        compos = compos.exclude(pk__in=pkeys)

    # we have to sort on the server due to paging
    compos = compos.order_by('-start_date')

    return compoRequest(request, compos)

@json_login_required
def ajax_owned(request):
    # only show bookmarked items
    # we have to sort on the server due to paging
    compos = request.user.get_profile().competitions_bookmarked.order_by('-start_date')
    return compoRequest(request, compos)

@login_required
def create(request):
    prof = request.user.get_profile()
    err_msg = ""
    if request.method == 'POST':
        form = CreateCompetitionForm(request.POST)
        if form.is_valid() and request.user.is_authenticated():
            # create and save the Competition
            comp = Competition()
            comp.title = form.cleaned_data.get('title')
            comp.host = request.user

            comp.preview_theme = form.cleaned_data.get('preview_theme', False)
            if form.cleaned_data.get('have_theme', False):
                comp.theme = form.cleaned_data.get('theme', '')

            comp.preview_rules = form.cleaned_data.get('preview_rules', False)
            if form.cleaned_data.get('have_rules', False):
                comp.rules = form.cleaned_data.get('rules', '')

            tz_offset = form.cleaned_data.get('tz_offset')
            tz_delta = timedelta(hours=tz_offset)

            comp.start_date = form.cleaned_data.get('start_date') + tz_delta
            comp.submit_deadline = form.cleaned_data.get('submission_deadline_date') + tz_delta

            # calculate vote deadline 
            quantity = int(form.cleaned_data.get('vote_time_quantity'))
            quantifier = int(form.cleaned_data.get('vote_time_measurement'))

            multiplier = {
                HOURS: 60*60,
                DAYS: 24*60*60,
                WEEKS: 7*24*60*60,
            }
            
            comp.vote_period_length = quantity * multiplier[quantifier]
            vote_period_delta = timedelta(seconds=comp.vote_period_length)

            comp.have_listening_party = form.cleaned_data.get('have_listening_party', True)
            if comp.have_listening_party:
                if form.cleaned_data.get('party_immediately'):
                    comp.listening_party_start_date = comp.submit_deadline
                else:
                    comp.listening_party_start_date = form.cleaned_data.get('listening_party_date') + tz_delta
                # initialize end date to start date. we make modifications to it
                # when entries are submitted.
                comp.listening_party_end_date = comp.listening_party_start_date

                # this changes whenever listening_party_end_date changes.
                comp.vote_deadline = comp.listening_party_end_date + vote_period_delta
            else:
                comp.vote_deadline = comp.submit_deadline + vote_period_delta

            # create a chatroom for it
            chatroom = ChatRoom()
            chatroom.permission_type = OPEN
            # open the chat room an hour before the competition
            chatroom.start_date = comp.start_date - timedelta(hours=1)
            # chat room is open an hour before and after competition
            chatroom.end_date = comp.listening_party_end_date + timedelta(hours=1)
            chatroom.save()
            comp.chat_room = chatroom;

            comp.save()


            # automatically bookmark it
            prof.competitions_bookmarked.add(comp)
            prof.save();

            return HttpResponseRedirect(reverse("arena.home"))
    else:
        initial = {
            'have_theme': True,
            'have_rules': True,
            'preview_rules': True,
            'have_listening_party': True,
            'party_immediately': True,
            'vote_time_quantity': 1,
            'vote_time_measurement': WEEKS,
        }
        form = CreateCompetitionForm(initial=initial)
    
    return render_to_response('arena/create.html', locals(),
        context_instance=RequestContext(request))

def competition(request, id):
    competition = get_object_or_404(Competition, id=int(id))
    return render_to_response('arena/competition.html', locals(),
        context_instance=RequestContext(request))

@json_login_required
def ajax_vote(request, entry_id):
    data = {'success': False}

    try:
        entry_id = int(entry_id)
    except ValueError:
        entry_id = 0
    entry = get_object_or_404(Entry, id=entry_id)

    # can't vote for yourself
    if entry.owner == request.user:
        data['reason'] = design.cannot_vote_for_yourself
        return json_response(data)

    # how many thumbs up should they have
    max_votes = max_vote_count(entry.competition.entry_set.count())
    used_votes = ThumbsUp.objects.filter(owner=request.user, entry__competition=entry.competition).count()

    if used_votes < max_votes:
        # OK! spend a vote on this entry
        vote = ThumbsUp()
        vote.owner = request.user
        vote.entry = entry
        vote.save()

        data['success'] = True
    else:
        data['reason'] = design.no_votes_left

    return json_response(data)

@json_login_required
def ajax_unvote(request, entry_id):
    data = {'success': False}

    try:
        entry_id = int(entry_id)
    except ValueError:
        entry_id = 0
    entry = get_object_or_404(Entry, id=entry_id)

    votes = ThumbsUp.objects.filter(owner=request.user, entry=entry)
    if votes.count() > 0:
        votes[0].delete()

    data['success'] = True
    return json_response(data)

