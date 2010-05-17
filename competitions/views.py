from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.template import RequestContext, Context, Template
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.models import model_to_dict
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Count

from opensourcemusic import settings
from opensourcemusic.main.views import safe_model_to_dict, json_response
from opensourcemusic.competitions.models import *
from opensourcemusic.competitions.forms import *
from opensourcemusic.chat.models import *

from datetime import datetime, timedelta
import tempfile
import os
import stat
import string

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import shutil

import waveform

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

    # break into title and extension
    parts = clean.split(".")
    if len(parts) > 0:
        clean = ".".join(parts[:-1])
        ext = "." + parts[-1]
    else:
        ext = ""
    
    if os.path.exists(os.path.join(path, clean + ext)):
        # use digits
        suffix = 2
        while os.path.exists(os.path.join(path, clean + str(suffix) + ext)):
            suffix += 1
        unique = clean + str(suffix) + ext
    else:
        unique = clean + ext

    return (os.path.join(path,unique), unique)

def ajax_submit_entry(request):
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
    except ValueError:
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

    # make sure files are small enough
    if mp3_file.size > settings.FILE_UPLOAD_SIZE_CAP:
        data['reason'] = 'MP3 file is too large.'
        return json_response(data)

    if not source_file is None:
        if source_file.size > settings.FILE_UPLOAD_SIZE_CAP:
            data['reason'] = 'Project source file is too large.'
            return json_response(data)

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
    profile = request.user.get_profile()
    artist_name = profile.solo_band.title
    audio['title'] = title
    audio['album'] = compo.title
    audio['artist'] = artist_name
    try:
        audio.save()
    except:
        data['reason'] = 'Unable to save ID3 tags.'
        return json_response(data)

    # pick a nice safe unique path for mp3_file, source_file, and wave form
    mp3_file_title = "%s - %s (%s).mp3" % (artist_name, title, compo.title)
    mp3_safe_path, mp3_safe_title = safe_file(os.path.join(settings.MEDIA_ROOT, 'compo', 'mp3'), mp3_file_title)
    mp3_safe_path_relative = os.path.join('compo','mp3',mp3_safe_title)

    png_file_title = "%s - %s (%s).png" % (artist_name, title, compo.title)
    png_safe_path, png_safe_title = safe_file(os.path.join(settings.MEDIA_ROOT, 'compo', 'mp3'), png_file_title)
    png_safe_path_relative = os.path.join('compo','mp3',png_safe_title)


    # move the mp3 file
    shutil.move(handle.name, mp3_safe_path)
    # give it read permissions
    os.chmod(mp3_safe_path, stat.S_IWUSR|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)

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
    song = Song()

    # upload the source file
    if not source_file is None:
        # extension of the source file
        parts = source_file.name.split('.')
        if len(parts) > 0:
            source_ext = parts[-1]
            source_file_title = "%s - %s (%s).%s" % (artist_name, title, compo.title, source_ext)
        else:
            source_file_title = "%s - %s (%s)" % (artist_name, title, compo.title)
        source_safe_path, source_safe_file_title = safe_file(os.path.join(settings.MEDIA_ROOT, 'compo', 'mp3'), source_file_title)
        source_safe_path_relative = os.path.join('compo','mp3',source_safe_file_title)

        upload_file(source_file, source_safe_path)
        song.source_file = source_safe_path_relative

    # generate the waveform image
    try:
        waveform.draw(mp3_safe_path, png_safe_path, (800, 100), fgColor=(157,203,229,255))
        song.waveform_img = png_safe_path_relative
    except:
        pass

    song.mp3_file = mp3_safe_path_relative
    song.band = request.user.get_profile().solo_band
    song.owner = request.user
    song.title = title
    song.length = audio_length
    song.comments = comments
    song.save()

    entry.competition = compo
    entry.owner = request.user
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
        'compo': compo_to_dict(compo, request.user),
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
        d['owner']['solo_band'] = safe_model_to_dict(entry.owner.get_profile().solo_band)
        d['song'] = safe_model_to_dict(entry.song)
        d['song']['band'] = safe_model_to_dict(entry.song.band)
        if compo_closed:
            d['vote_count'] = ThumbsUp.objects.filter(entry=entry).count()
        return d

    if compo_closed:
        entries = compo.entry_set.annotate(vote_count=Count('thumbsup')).order_by('-vote_count')
    else:
        entries = compo.entry_set.order_by('submit_date')
    data['entries'] = [add_to_entry(x) for x in entries]

    if request.user.is_authenticated():
        max_votes = max_vote_count(compo.entry_set.count())
        used_votes = ThumbsUp.objects.filter(owner=request.user, entry__competition=compo)

        data['user'] = safe_model_to_dict(request.user)
        data['user']['is_authenticated'] = True
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

    compos = compos.order_by('-start_date')

    return compoRequest(request, compos)

def ajax_owned(request):
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
    }

    if not request.user.is_authenticated():
        return json_response(data)

    # only show bookmarked items
    compos = request.user.get_profile().competitions_bookmarked.order_by('start_date')
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
            chatroom.end_date = comp.vote_deadline + timedelta(hours=1)
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
    
    url = reverse("arena.create")
    return render_to_response(url, locals(), context_instance=RequestContext(request))

def competition(request, id):
    competition = get_object_or_404(Competition, id=int(id))
    url = reverse("arena.compete")
    return render_to_response(url, locals(), context_instance=RequestContext(request))

def ajax_vote(request, entry_id):
    data = {'success': False}

    try:
        entry_id = int(entry_id)
    except ValueError:
        entry_id = 0
    entry = get_object_or_404(Entry, id=entry_id)

    if not request.user.is_authenticated():
        data['reason'] = "Not authenticated."
        return json_response(data)

    # can't vote for yourself
    if entry.owner == request.user:
        data['reason'] = "Can't vote for yourself."
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
        data['reason'] = "No votes left."

    return json_response(data)

def ajax_unvote(request, entry_id):
    data = {'success': False}

    try:
        entry_id = int(entry_id)
    except ValueError:
        entry_id = 0
    entry = get_object_or_404(Entry, id=entry_id)

    if not request.user.is_authenticated():
        data['reason'] = "Not authenticated."
        return json_response(data)

    votes = ThumbsUp.objects.filter(owner=request.user, entry=entry)
    if votes.count() > 0:
        votes[0].delete()

    data['success'] = True
    return json_response(data)

