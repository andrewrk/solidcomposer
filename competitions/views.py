from chat.models import ChatRoom
from competitions import design
from competitions.forms import CreateCompetitionForm, TimeUnit
from competitions.models import Competition, Entry, ThumbsUp
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from main.common import json_login_required, json_post_required, json_failure, \
    json_response, get_obj_from_request, get_val
from main.uploadsong import upload_song, handle_project_upload
from workshop.models import Project, ProjectVersion, SampleDependency

@json_login_required
@json_post_required
def ajax_submit_entry(request):
    compo = get_obj_from_request(request.POST, 'compo', Competition)
    if compo is None:
        return json_failure(design.competition_not_found)

    # make sure it's still submission time
    now = datetime.now()
    if now >= compo.submit_deadline:
        return json_failure(design.past_submission_deadline)

    if now <= compo.start_date:
        return json_failure(design.competition_not_started)

    title = request.POST.get('entry-title','')
    comments = request.POST.get('entry-comments', '')
    mp3_file = request.FILES.get('entry-file-mp3')
    source_file = request.FILES.get('entry-file-source')
    is_open_source = request.POST.get('entry-open-source', False)

    entries = Entry.objects.filter(owner=request.user, competition=compo)
    resubmitting = entries.count() > 0

    # make sure files are small enough
    if not resubmitting and mp3_file is None:
        return json_failure(design.mp3_required)

    if mp3_file is not None and mp3_file.size > settings.FILE_UPLOAD_SIZE_CAP:
        return json_failure(design.mp3_too_big)

    if source_file is not None:
        if source_file.size > settings.FILE_UPLOAD_SIZE_CAP:
            return json_failure(design.source_file_too_big)

    if title == '':
        return json_failure(design.entry_title_required)

    if mp3_file is not None:
        band = request.user.get_profile().solo_band

        if resubmitting:
            entry = entries[0]
            project = Project.objects.get(latest_version__song=entry.song)
            new_version_number = project.latest_version.version + 1
            filename_appendix = "_" + str(new_version_number)
        else:
            filename_appendix = ""

        result = upload_song(request.user,
            file_mp3_handle=mp3_file,
            file_source_handle=source_file, 
            max_song_len=settings.COMPO_ENTRY_MAX_LEN,
            band=band,
            song_title=title,
            song_album=compo.title,
            song_comments=comments,
            filename_appendix=filename_appendix)

        if not result['success']:
            return json_failure(result['reason'])

        song = result['song']
        song.is_open_source = is_open_source
        song.is_open_for_comments = True
        song.save()

        # make a new version and attach that to the entry
        if resubmitting:

            # create new version
            version = ProjectVersion()
            version.project = project
            version.song = song
            version.version = new_version_number
            version.saveNewVersion()

            old_length = entry.song.length
            buffer_time = 0
        else:
            # create the project
            project = Project()
            project.band = band
            project.save()

            # create the first version
            version = ProjectVersion()
            version.project = project
            version.song = song
            version.version = 1
            version.saveNewVersion()

            # subscribe the creator
            project.subscribers.add(request.user)
            project.save()

            # create new entry
            entry = Entry()
            entry.competition = compo
            entry.owner = request.user

            old_length = 0
            buffer_time = settings.LISTENING_PARTY_BUFFER_TIME

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
    else:
        # only providing source and possibly renaming.
        entry = entries[0]
        song = entry.song

        if source_file is not None:
            handle_project_upload(source_file, request.user, song)

        song.title = title
        song.is_open_source = is_open_source
        song.comments = comments
        song.save()

    return json_response({'success': True})

def max_vote_count(entry_count):
    """
    given how many entrants there are, compute how many votes each person gets.
    """
    x = int(entry_count / 3)
    if x < 1:
        x = 1

    return x

def song_to_dict(song, user):
    d = song.to_dict(chains=['owner', 'studio', 'band', 'comment_node'])
    if song.studio is not None and d.has_key('studio'):
        d['studio']['logo_16x16'] = song.studio.logo_16x16.url

        if user.is_authenticated():
            profile = user.get_profile()

            d['studio']['missing'] = song.studio not in profile.studios.all()

            def sample_to_dict(x):
                d = x.to_dict()
                d['missing'] = x.uploaded_sample is None
                return d

            d['samples'] = [sample_to_dict(x) for x in SampleDependency.objects.filter(song=song)]

            owned_plugins = profile.plugins.all()
            def plugin_to_dict(x):
                d = x.to_dict()
                d['missing'] = x not in owned_plugins
                return d

            d['plugins'] = [plugin_to_dict(x) for x in song.plugins.all()]

    return d
    
def ajax_compo(request, compo_id):
    compo_id = int(compo_id)
    try:
        compo = get_object_or_404(Competition, pk=compo_id)
    except Competition.DoesNotExist:
        return json_failure(design.competition_not_found)

    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
        'compo': compo_to_dict(compo, request.user),
        'party': {
            'buffer_time': settings.LISTENING_PARTY_BUFFER_TIME,
        }
    }

    if request.user.is_authenticated():
        max_votes = max_vote_count(compo.entry_set.count())
        used_votes = ThumbsUp.objects.filter(owner=request.user, entry__competition=compo)

        data['user'].update(request.user.get_profile().to_dict());
        data['votes'] = {
            'max': max_votes,
            'used': [x.to_dict() for x in used_votes],
            'left': max_votes - used_votes.count(),
        }
        user_entries = Entry.objects.filter(competition=compo, owner=request.user)
        data['submitted'] = (user_entries.count() > 0)

    def entry_to_dict(entry):
        data = entry.to_dict(chains=['owner.solo_band'])
        data['song'] = song_to_dict(entry.song, request.user)
        if request.user.is_authenticated() and entry.owner == request.user:
            version = ProjectVersion.objects.get(song=entry.song)
            data['project_id'] = version.project.pk
            data['version_number'] = version.version
        return data

    # entries. if competition is closed, sort by vote count.
    data['entries'] = [entry_to_dict(x) for x in compo.entry_set.all()]

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
    data = compo.to_dict(chains=['host'])

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
    page_number = get_val(request.GET, 'page', 1)
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
                TimeUnit.HOURS: 60*60,
                TimeUnit.DAYS: 24*60*60,
                TimeUnit.WEEKS: 7*24*60*60,
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
            chatroom.permission_type = ChatRoom.OPEN
            # open the chat room an hour before the competition
            chatroom.start_date = comp.start_date - timedelta(hours=1)
            # chat room is open an hour before and after competition
            chatroom.end_date = comp.listening_party_end_date + timedelta(hours=1)
            chatroom.save()
            comp.chat_room = chatroom;

            comp.save()


            # automatically bookmark it
            prof.competitions_bookmarked.add(comp)
            prof.save()

            return HttpResponseRedirect(reverse("arena.home"))
    else:
        initial = {
            'have_theme': True,
            'have_rules': True,
            'preview_rules': True,
            'have_listening_party': True,
            'party_immediately': True,
            'vote_time_quantity': 1,
            'vote_time_measurement': TimeUnit.WEEKS,
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

