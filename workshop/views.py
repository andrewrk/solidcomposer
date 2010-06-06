from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response, get_object_or_404

from workshop.models import *
from workshop.forms import *
from workshop import design
from main.models import *
from main.common import *
from main.uploadsong import upload_song

DEFAULT_FILTER = 'all'
JFILTERS = {
    'all': {
        'caption': "All",
    },
    'available': {
        'caption': "Available",
    },
    'out': {
        'caption': "Checked out", 
    },
    'mine': {
        'caption': "Checked out to me", 
    },
    'scrapped': {
        'caption': "Scrapped", 
    },
}

FILTERS = dict(JFILTERS)
FILTERS['all']['func'] = lambda projects: filterVisible(projects)
FILTERS['available']['func'] = lambda projects: filterVisible(projects).filter(checked_out_to=None)
FILTERS['out']['func'] = lambda projects: filterVisible(projects).exclude(checked_out_to=None)
FILTERS['mine']['func'] = lambda projects, user: filterVisible(projects).filter(checked_out_to=user)
FILTERS['scrapped']['func'] = lambda projects: filterScrapped(projects)


def filterVisible(projects):
    return projects.filter(visible=True)

def filterScrapped(projects):
    return projects.filter(visible=False)

def ajax_home(request):
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
        'success': True,
    }


    if data['user']['is_authenticated']:
        data['user'].update(safe_model_to_dict(request.user))

        # bands the user is a part of
        def band_data(member):
            d = safe_model_to_dict(member.band)
            d['role'] = member.role
            return d
        members = BandMember.objects.filter(user=request.user)
        data['bands'] = [band_data(x) for x in members]

        # invitations
        def invite_data(invite):
            d = safe_model_to_dict(invite)
            d['band'] = safe_model_to_dict(invite.band)
            return d
        invites = BandInvitation.objects.filter(invitee=request.user)
        data['invites'] = [invite_data(x) for x in invites]


    return json_response(data)

def handle_invite(request, accept):
    data = {'success': False}

    invitation_id_str = request.GET.get("invitation", 0)
    try:
        invitation_id = int(invitation_id_str)
    except ValueError:
        invitation_id = 0

    invite = get_object_or_404(BandInvitation, id=invitation_id)

    # make sure the user has permission to reject this invitation
    if invite.invitee != request.user:
        data['reason'] = "This invitation was not sent to you."
        return json_response(data)

    if accept:
        # apply the invitation
        member = BandMember()
        member.user = request.user
        member.band = invite.band
        member.role = invite.role
        member.save()

    invite.delete()
        
    data['success'] = True
    return json_response(data)

@json_login_required
def ajax_accept_invite(request):
    return handle_invite(request, accept=True)
    
@json_login_required
def ajax_ignore_invite(request):
    return handle_invite(request, accept=False)

def band(request, band_id_str):
    band_id = int(band_id_str)
    band = get_object_or_404(Band, id=band_id)
    return render_to_response('workbench/band.html', {
            "band": band,
        }, context_instance=RequestContext(request))

@json_login_required
@json_get_required
def ajax_project_filters(request):
    band_id_str = request.GET.get("band", 0)
    try:
        band_id = int(band_id_str)
    except ValueError:
        band_id = 0

    try:
        band = Band.objects.get(pk=band_id)
    except:
        return json_failure(design.bad_band_id)

    if not band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    projects = Project.objects.filter(band=band)

    results = dict(JFILTERS)
    for filterId, filterData in results.iteritems():
        filterData['count'] = performFilter(filterId, projects, request.user).count()

    return json_success(results)

def performFilter(filterId, projects, user=None):
    if filterId == 'mine':
        assert user is not None
        return FILTERS[filterId]['func'](projects, user)

    return FILTERS[filterId]['func'](projects)

def user_to_dict(x):
    from workshop import design
    d = safe_model_to_dict(x)
    d['gravatar'] = gravatar_url(x.email, design.project_gravatar_size)
    d['get_profile']['get_points'] = x.get_profile().get_points()
    return d

def song_to_dict(x, user):
    d = safe_model_to_dict(x)
    d['owner'] = user_to_dict(x.owner)
    if x.studio:
        d['studio'] = safe_model_to_dict(x.studio)
        d['studio']['logo_16x16'] = x.studio.logo_16x16.url
    else:
        d['studio'] = None

    allSamples = x.samples.all()
    allEffects = x.effects.all()
    allGenerators = x.generators.all()
    d['samples'] = [safe_model_to_dict(y) for y in allSamples]
    d['effects'] = [safe_model_to_dict(y) for y in allEffects]
    d['generators'] = [safe_model_to_dict(y) for y in allGenerators]

    ownedEffects = user.get_profile().effects.all()
    ownedGenerators = user.get_profile().generators.all()
    d['missing_samples'] = [safe_model_to_dict(y) for y in filter(lambda x: x.sample_file is None, allSamples)]
    d['missing_generators'] = [safe_model_to_dict(y) for y in filter(lambda x: x not in ownedGenerators, allGenerators)]
    d['missing_effects'] = [safe_model_to_dict(y) for y in filter(lambda x: x not in ownedEffects, allEffects)]
    return d
    
def version_to_dict(x, user):
    d = {
        'song': song_to_dict(x.song, user),
        'version': x.version,
    }
    return d

def project_to_dict(x, user):
    d = {
        'latest_version': version_to_dict(x.latest_version, user),
        'date_activity': x.date_activity,
        'checked_out_to': None,
        'visible': x.visible,
        'tags': [safe_model_to_dict(tag) for tag in x.tags.all()],
        'scrap_voters': x.scrap_voters.count(),
        'promote_voters': x.promote_voters.count(),
        'id': x.id,
        'band': safe_model_to_dict(x.band),
    }
    if x.checked_out_to is not None:
        d['checked_out_to'] = safe_model_to_dict(x.checked_out_to)

    return d

@json_login_required
@json_get_required
def ajax_project_list(request):
    # validate input
    page_str = request.GET.get('page', 1) 
    try:
        page_number = int(page_str)
    except ValueError:
        page_number = 1

    filterName = request.GET.get('filter', 'all')
    if not FILTERS.has_key(filterName):
        filterName = DEFAULT_FILTER

    searchText = request.GET.get('search', '')

    band_str = request.GET.get('band', 0)
    try:
        band_id = int(band_str)
    except ValueError:
        band_id = 0

    try:
        band = Band.objects.get(pk=band_id)
    except:
        return json_failure(design.bad_band_id)

    if not band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    # get a list of filtered projects 
    projects = performFilter(filterName, Project.objects.filter(band=band), request.user)
    
    # apply search text to query
    if searchText:
        # limit to 10 words
        words = searchText.split()[:10]
        for word in words:
            projects = projects.filter(title__icontains=word)

    paginator = Paginator(projects, settings.ITEMS_PER_PAGE)

    # build the json object

    data = {
        'projects': [project_to_dict(x, request.user) for x in paginator.page(page_number).object_list],
        'page_count': paginator.num_pages,
        'page_number': page_number,
        'band': safe_model_to_dict(band),
    }

    return json_success(data)

@json_login_required
@json_get_required
def ajax_project(request):
    """
    return the project history. if a last_version is supplied, only
    return newer ones. Also return the current state - who has it
    checked out, etc.
    """
    last_version_str = request.GET.get('last_version', 'null')
    project_id = request.GET.get('project', 0)
    try:
        project_id = int(project_id)
    except ValueError:
        project_id = 0
    project = get_object_or_404(Project, id=project_id)

    # make sure the user has permission
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'has_permission': project.band.permission_to_work(request.user),
        },
        'success': False,
    }

    if not data['user']['has_permission']:
        data['reason'] = design.you_dont_have_permission_to_work_on_this_band
        return json_response(data)

    data['project'] = project_to_dict(project, request.user)

    if last_version_str == 'null':
        # get entire version list
        data['versions'] = [version_to_dict(x, request.user) for x in ProjectVersion.objects.filter(project=project)]
    else:
        try:
            last_version_id = int(last_version_str)
        except ValueError:
            last_version_id = 0
        data['versions'] = [version_to_dict(x, request.user) for x in ProjectVersion.objects.filter(project=project, id__gt=last_version_id)]

    data['user'].update(user_to_dict(request.user))

    data['success'] = True
    return json_response(data)

@json_login_required
@json_post_required
def ajax_create_band(request):
    data = {
        'success': False,
    }

    form = NewBandForm(request.POST)
    if form.is_valid():
        band = Band()
        band.title = form.cleaned_data.get('band_name')
        band.create_paths()
        band.save()

        manager = BandMember()
        manager.user = user
        manager.band = band
        manager.role = MANAGER
        manager.save()
    else:
        data['reason'] = "\n".join(['%s: %s' % (k, v) for k, v in form.errors])
        return json_response(data)
    
    data['success'] = True
    return json_response(data)

@login_required
def band_settings(request, band_id_str):
    "todo"
    pass

@login_required
def project(request, band_id_str, project_id_str):
    try:
        band_id = int(band_id_str)
    except ValueError:
        band_id = 0
    try:
        project_id = int(project_id_str)
    except ValueError:
        project_id = 0

    band = get_object_or_404(Band, id=band_id)
    project = get_object_or_404(Project, id=project_id)
    return render_to_response('workbench/project.html', locals(), context_instance=RequestContext(request))

@login_required
def create_project(request, band_str):
    band_id = int(band_str)
    band = get_object_or_404(Band, id=band_id)
    err_msg = ''
    if request.method == 'POST':
        form = NewProjectForm(request.POST, request.FILES)
        if form.is_valid():
            prof = request.user.get_profile()

            mp3_file = request.FILES.get('file_mp3')
            source_file = request.FILES.get('file_source')

            # make sure we have not hit the user's quota
            new_used_space = prof.used_space + mp3_file.size + source_file.size
            if new_used_space > prof.total_space:
                err_msg = design.reached_upload_quota
            else:
                # upload the song
                result = upload_song(request.user,
                    file_mp3_handle=mp3_file,
                    file_source_handle=source_file, 
                    band=band,
                    song_title=form.cleaned_data.get('title'))
                if not result['success']:
                    err_msg = result['reason']
                else:
                    # fill in the rest of the fields
                    song = result['song']
                    song.comments = form.cleaned_data.get('comments', '')
                    song.save()

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

                    return HttpResponseRedirect(reverse("workbench.project", args=[band.id, project.id]))
    else:
        form = NewProjectForm()
    return render_to_response('workbench/new_project.html', {
            'form': form,
            'err_msg': err_msg,
        }, context_instance=RequestContext(request))
    
