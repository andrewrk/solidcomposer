from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Count

from opensourcemusic.competitions.models import *
from opensourcemusic import settings
from opensourcemusic.main.views import safe_model_to_dict, json_response
from opensourcemusic.competitions.forms import *

from datetime import datetime, timedelta
import tempfile
import os
import stat
import string

def upload_file(f, new_name):
    handle = open(new_name, 'wb+')
    upload_file_h(f, handle)
    handle.close()
    os.chmod(new_name, stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)

def upload_file_h(f, handle):
    for chunk in f.chunks():
        handle.write(chunk)

def safe_file(path, title):
    """
    returns a tuple (title joined with path, only title). paths are guaranteed
    to be unique and safe.
    """
    allowed = string.letters + string.digits + "_-."
    clean = ""
    for c in title:
        if c in allowed:
            clean += c
        else:
            clean += "_"

    return (os.path.join(path,clean), clean)

def ajax_submit_entry(request):
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3
    import shutil

    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
        'success': False,
        'reason': 'Not authenticated',
    }
    if not request.user.is_authenticated():
        return json_response(data)

    if request.method != 'POST':
        data['reason'] = 'Must submit via POST.'
        return json_response(data)

    compo_id = request.POST.get('compo', 0)
    try:
        compo_id = int(compo_id)
    except:
        compo_id = 0
    
    try:
        compo = Competition.objects.get(pk=compo_id)
    except Competition.DoesNotExist:
        data['reason'] = 'Competition not found'
        return json_response(data)

    # make sure it's still submission time
    now = datetime.now()
    if now >= compo.submit_deadline:
        data['reason'] = 'Past submission deadline.'
        return json_response(data)

    if now <= compo.start_date:
        data['reason'] = 'Competition has not yet begun.'
        return json_response(data)

    title = request.POST.get('entry-title','')
    comments = request.POST.get('entry-comments')
    mp3_file = request.FILES.get('entry-file-mp3')
    source_file = request.FILES.get('entry-file-source')

    if title == '':
        data['reason'] = 'Entry title is required.'
        return json_response(data)

    if mp3_file is None:
        data['reason'] = 'MP3 file submission is required.'
        return json_response(data)

    # upload mp3_file to temp folder
    handle = tempfile.NamedTemporaryFile(suffix='mp3', delete=False)
    upload_file_h(mp3_file, handle)
    handle.close()

    # read the length tag
    try:
        audio = MP3(handle.name, ID3=EasyID3)
        audio_length = audio.info.length
    except:
        data['reason'] = 'Invalid MP3 file.'
        return json_response(data)

    # reject if too long or invalid
    if audio.info.sketchy:
        data['reason'] = 'Sketchy MP3 file.'
        return json_response(data)

    if audio.info.length > settings.COMPO_ENTRY_MAX_LEN:
        data['reason'] = 'Song is too long.'
        return json_response(data)

    # enforce ID3 tags
    audio['title'] = title
    audio['album'] = compo.title
    audio['artist'] = request.user.get_profile().artist_name
    try:
        audio.save()
    except:
        data['reason'] = 'Unable to save ID3 tags.'
        return json_response(data)

    # pick a nice safe unique path for mp3_file and source_file
    mp3_file_title = "%s - %s (%s).mp3" % (request.user.get_profile().artist_name, title, compo.title)
    mp3_safe_path, mp3_safe_title = safe_file(os.path.join(settings.MEDIA_ROOT, 'compo', 'mp3'), mp3_file_title)
    mp3_safe_path_relative = os.path.join('compo','mp3',mp3_safe_title)

    # move the mp3 file
    shutil.move(handle.name, mp3_safe_path)
    # give it read permissions
    os.chmod(mp3_safe_path, stat.S_IWUSR|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)

    entries = Entry.objects.filter(owner=request.user.get_profile(), competition=compo)
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
    song = Song()

    # upload the source file
    if not source_file is None:
        # extension of the source file
        parts = source_file.name.split('.')
        if len(parts) > 0:
            source_ext = parts[-1]
            source_file_title = "%s - %s (%s).%s" % (request.user.get_profile().artist_name, title, compo.title, source_ext)
        else:
            source_file_title = "%s - %s (%s)" % (request.user.get_profile().artist_name, title, compo.title)
        source_safe_path, source_safe_file_title = safe_file(os.path.join(settings.MEDIA_ROOT, 'compo', 'mp3'), source_file_title)
        source_safe_path_relative = os.path.join('compo','mp3',source_safe_file_title)

        upload_file(source_file, source_safe_path)
        song.source_file = source_safe_path_relative

    song.mp3_file = mp3_safe_path_relative
    song.owner = request.user.get_profile()
    song.title = title
    song.length = audio_length
    song.comments = comments
    song.save()

    entry.competition = compo
    entry.owner = request.user.get_profile()
    entry.song = song
    entry.save()

    # update competition dates based on this newfound length 
    vote_period_delta = timedelta(seconds=compo.vote_period_length)
    if compo.have_listening_party:
        compo.listening_party_end_date += timedelta(seconds=(audio_length-old_length+buffer_time))
        compo.vote_deadline = compo.listening_party_end_date + vote_period_delta
    else:
        compo.vote_deadline = compo.submit_deadline + vote_period_delta
    compo.save()

    chatroom = compo.chat_room
    chatroom.end_date = compo.vote_deadline + timedelta(hours=1)
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
            'is_authenticated': False,
        },
        'compo': safe_model_to_dict(compo),
        'party': {
            'buffer_time': settings.LISTENING_PARTY_BUFFER_TIME,
        }
    }

    # entries. if competition is closed, sort by vote count.
    now = datetime.now()
    compo_closed = (now > compo.vote_deadline)
    def add_to_entry(entry):
        d = safe_model_to_dict(entry)
        d['owner'] = safe_model_to_dict(entry.owner)
        d['song'] = safe_model_to_dict(entry.song)
        if compo_closed:
            d['vote_count'] = ThumbsUp.objects.filter(entry=entry).count()
        return d

    if compo_closed:
        entries = compo.entry_set.annotate(vote_count=Count('thumbsup')).order_by('-vote_count')
    else:
        entries = compo.entry_set.order_by('submit_date')
    data['entries'] = [add_to_entry(x) for x in entries]

    data['compo']['have_theme'] = compo.theme != ''
    data['compo']['have_rules'] = compo.rules != ''

    # send the rules and theme if it's time
    compo_started = compo.start_date <= now
    if compo_started or compo.preview_theme:
        data['compo']['theme'] = compo.theme
    if compo_started or compo.preview_rules:
        data['compo']['rules'] = compo.rules

    if request.user.is_authenticated():
        max_votes = max_vote_count(compo.entry_set.count())
        used_votes = ThumbsUp.objects.filter(owner=request.user.get_profile(), entry__competition=compo)

        data['user'] = safe_model_to_dict(request.user)
        data['user']['get_profile'] = request.user.get_profile()
        data['user']['is_authenticated'] = True
        data['votes'] = {
            'max': max_votes,
            'used': [safe_model_to_dict(x) for x in used_votes],
            'left': max_votes - used_votes.count(),
        }
        user_entries = Entry.objects.filter(competition=compo, owner=request.user.get_profile())
        data['submitted'] = (user_entries.count() > 0)
        if user_entries.count() > 0:
            data['user_entry'] = safe_model_to_dict(user_entries[0].song)

    return json_response(data)

def ajax_unbookmark(request, id):
    id = int(id)
    data = {'success': False}
    if request.user.is_authenticated():
        comp = get_object_or_404(Competition, id=id)
        prof = request.user.get_profile()
        prof.competitions_bookmarked.remove(comp)
        prof.save()
        data['success'] = True

    return json_response(data)

def ajax_bookmark(request, id):
    data = {'success': False}
    if request.user.is_authenticated():
        comp = get_object_or_404(Competition, id=int(id))
        prof = request.user.get_profile()
        prof.competitions_bookmarked.add(comp)
        prof.save()
        data['success'] = True

    return json_response(data)

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

    return json_response(data)

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
        return json_response(data)

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

    return json_response(data)

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
            comp.host = prof

            comp.preview_theme = form.cleaned_data.get('preview_theme', False)
            if form.cleaned_data.get('have_theme', False):
                comp.theme = form.cleaned_data.get('theme', '')

            comp.preview_rules = form.cleaned_data.get('preview_rules', False)
            if form.cleaned_data.get('have_rules', False):
                comp.rules = form.cleaned_data.get('rules', '')


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
            vote_period_delta = timedelta(seconds=comp.vote_period_length)

            comp.have_listening_party = form.cleaned_data.get('have_listening_party', True)
            if comp.have_listening_party:
                comp.listening_party_start_date = form.cleaned_data.get('listening_party_date')
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
            chatroom.end_date = comp.vote_deadline + timedelta(hours=1)
            chatroom.save()
            comp.chat_room = chatroom;

            comp.save()


            # automatically bookmark it
            prof.competitions_bookmarked.add(comp)
            prof.save();

            return HttpResponseRedirect('/arena/')
    else:
        form = CreateCompetitionForm()
    
    return render_to_response('arena/create.html', locals(), context_instance=RequestContext(request))

def competition(request, id):
    competition = get_object_or_404(Competition, id=int(id))
    return render_to_response('arena/competition.html', locals(), context_instance=RequestContext(request))

def ajax_vote(request, entry_id):
    data = {'success': False}

    try:
        entry_id = int(entry_id)
    except:
        entry_id = 0
    entry = get_object_or_404(Entry, id=entry_id)

    if not request.user.is_authenticated():
        data['reason'] = "Not authenticated."
        return json_response(data)

    # can't vote for yourself
    if entry.owner == request.user.get_profile():
        data['reason'] = "Can't vote for yourself."
        return json_response(data)

    # how many thumbs up should they have
    max_votes = max_vote_count(entry.competition.entry_set.count())
    used_votes = ThumbsUp.objects.filter(owner=request.user.get_profile(), entry__competition=entry.competition).count()

    if used_votes < max_votes:
        # OK! spend a vote on this entry
        vote = ThumbsUp()
        vote.owner = request.user.get_profile()
        vote.entry = entry
        vote.save()

        data['success'] = True
    else:
        data['reason'] = "No votes left."

    return json_response(data)

def ajax_unvote(request, entry_id):
    data = {'success': False}

    try:
        entry_id = int(entry_id)
    except:
        entry_id = 0
    entry = get_object_or_404(Entry, id=entry_id)

    if not request.user.is_authenticated():
        data['reason'] = "Not authenticated."
        return json_response(data)

    votes = ThumbsUp.objects.filter(owner=request.user.get_profile(), entry=entry)
    if votes.count() > 0:
        votes[0].delete()

    data['success'] = True
    return json_response(data)

