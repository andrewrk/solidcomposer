from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response, get_object_or_404

from workshop.models import *
from workshop.forms import *
from main.models import *
from main.common import *
from main.upload import *
from workshop import design
from main.uploadsong import upload_song, studio_extensions, handle_sample_file, handle_mp3_upload, handle_project_upload

import zipfile
import tempfile
import shutil
import hashlib

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

def activity_list(request):
    """
    return the 10 newest log entries since the id supplied.
    """
    last_entry_id = get_val(request.GET, 'lastEntry', 0)
    entry_count = get_val(request.GET, 'count', 10)

    entries = LogEntry.objects.filter(band__pk__in=BandMember.objects.filter(user=request.user))
    if last_entry_id == 0:
        # get newest entry_count entries
        entries = entries.order_by('-timestamp')[:entry_count]
    else:
        # get only ones since last_entry_id
        entries = entries.filter(pk__gt=last_entry_id).order_by('-timestamp')[:entry_count]

    return [entry.to_dict(chains=['catalyst', 'target', 'version.project']) for entry in entries]

def ajax_home(request):
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
        'success': True,
    }


    if data['user']['is_authenticated']:
        data['user'].update(request.user.get_profile().to_dict())

        # bands the user is a part of
        members = BandMember.objects.filter(user=request.user)
        data['members'] = [x.to_dict(chains=['band']) for x in members]

        # invitations
        invites = BandInvitation.objects.filter(invitee=request.user)
        data['invites'] = [x.to_dict(chains=['band']) for x in invites]

        # log entries
        data['activity'] = activity_list(request)

    return json_response(data)

def handle_invite(request, accept):
    data = {'success': False}

    invite = get_obj_from_request(request.GET, 'invitation', BandInvitation)
    if invite is None:
        return HttpResponseNotFound()

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
    band = get_obj_from_request(request.GET, 'band', Band)

    if band is None:
        return json_failure(design.bad_band_id)

    if not band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    projects = Project.objects.filter(band=band)

    results = dict(JFILTERS)
    for filterId, filterData in results.iteritems():
        filterData['count'] = performFilter(filterId, projects, request.user).count()

    return json_success(results)

@json_login_required
@json_post_required
def ajax_dependency_ownership(request):
    profile = request.user.get_profile()

    dep_type_int = get_val(request.POST, 'dependency_type', -1)

    if dep_type_int == PluginDepenency.STUDIO:
        dep_type = Studio
        collection = profile.studios
    else:
        dep_type = PluginDepenency
        collection = profile.plugins

    dep = get_obj_from_request(request.POST, 'dependency_id', dep_type)

    if dep is None:
        return json_failure(design.bad_dependency_id)

    have = request.POST.get('have', False)
    if have == 'false':
        have = False

    if have:
        collection.add(dep)
    else:
        collection.remove(dep)

    profile.save()
    
    return json_success()

def performFilter(filterId, projects, user=None):
    if filterId == 'mine':
        assert user is not None
        return FILTERS[filterId]['func'](projects, user)

    return FILTERS[filterId]['func'](projects)


@json_login_required
@json_get_required
def ajax_project_list(request):
    # validate input
    page_number = get_val(request.GET, 'page', 1)

    filterName = request.GET.get('filter', 'all')
    if not FILTERS.has_key(filterName):
        filterName = DEFAULT_FILTER

    searchText = request.GET.get('search', '')

    band = get_obj_from_request(request.GET, 'band', Band)

    if band is None:
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

    def project_to_dict(project):
        data = project.to_dict(access=SerializableModel.OWNER, chains=['checked_out_to'])
        data['latest_version'] = version_to_dict(project.latest_version, request.user)
        return data

    member = BandMember.objects.get(band=band, user=request.user)

    # build the json object
    data = {
        'projects': [project_to_dict(x) for x in paginator.page(page_number).object_list],
        'page_count': paginator.num_pages,
        'page_number': page_number,
        'band': band.to_dict(access=SerializableModel.OWNER),
        'band_member': member.to_dict(),
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
    last_version_id = get_val(request.GET, 'last_version', 0)
    project = get_obj_from_request(request.GET, 'project', Project)

    if project is None:
        return json_failure(design.bad_project_id)

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

    data['project'] = project.to_dict(SerializableModel.OWNER, chains=['checked_out_to', 'band'])

    if last_version_id == 0:
        # get entire version list
        data['versions'] = [version_to_dict(x, request.user) for x in ProjectVersion.objects.filter(project=project)]
    else:
        data['versions'] = [version_to_dict(x, request.user) for x in ProjectVersion.objects.filter(project=project, id__gt=last_version_id)]

    data['user'].update(request.user.get_profile().to_dict())

    data['success'] = True
    return json_response(data)

def actually_create_band(user, band_name):
    band = Band()
    band.title = band_name
    band.total_space = settings.BAND_INIT_SPACE
    band.save()

    manager = BandMember()
    manager.user = user
    manager.band = band
    manager.role = BandMember.MANAGER
    manager.save()

@login_required
def create_band(request):
    if request.method == 'POST':
        form = NewBandForm(request.POST)
        if form.is_valid():
            actually_create_band(request.user, form.cleaned_data.get('band_name'))
            return HttpResponseRedirect(reverse("workbench.home"))
    else:
        form = NewBandForm()

    return render_to_response('workbench/create_band.html', {'form': form}, context_instance=RequestContext(request))

@json_login_required
@json_post_required
def ajax_create_band(request):
    form = NewBandForm(request.POST)

    if form.is_valid():
        actually_create_band(request.user, form.cleaned_data.get('band_name'))
        return json_success()

    return json_failure("\n".join(['%s: %s' % (k, v) for k, v in form.errors]))

def handle_sample_upload(fileHandle, user, band, callback=None):
    """
    uploads fileHandle, and runs handle_sample_file.
    """
    # copy it to temp file
    name, ext = os.path.splitext(fileHandle.name)

    handle = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    upload_file_h(fileHandle, handle)
    handle.close()

    path, title = os.path.split(fileHandle.name)
    handle_sample_file(handle.name, title, user, band, callback=callback)

@json_login_required
@json_post_required
def ajax_rename_project(request):
    """
    Make a new version that renames the project.
    """
    new_title = request.POST.get('title', '')
    comments  = request.POST.get('comments', '')
    
    if new_title == '':
        return json_failure(design.you_must_have_a_title)

    project = get_obj_from_request(request.POST, 'project', Project)

    if project is None:
        return json_failure(design.bad_project_id)

    if not project.band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    node = SongCommentNode()
    node.owner = request.user
    node.content = comments
    node.save()

    version = ProjectVersion()
    version.project = project
    version.owner = request.user
    version.comment_node = node
    version.version = project.latest_version.version # no +1 because only renaming
    version.new_title = new_title
    version.save()

    project.title = new_title
    project.save()

    return json_success()

@json_login_required
@json_post_required
def ajax_upload_samples_as_version(request):
    """
    Upload some samples and then add each uploaded sample
    to a new project version.
    """
    project = get_obj_from_request(request.POST, 'project', Project)
    comments = request.POST.get('comments', '')

    if project is None:
        return json_failure(design.bad_project_id)

    band = project.band

    if not band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    node = SongCommentNode()
    node.owner = request.user
    node.content = comments
    node.save()

    version = ProjectVersion()
    version.project = project
    version.owner = request.user
    version.comment_node = node
    version.version = project.latest_version.version # no +1, only adding samples.
    version.save() # so we can add provided_samples
    
    def add_sample_to_version(sample):
        version.provided_samples.add(sample)
        
    files = request.FILES.getlist('file')

    for item in files:
        handle_sample_upload(item, request.user, band, callback=add_sample_to_version)

    band.save()
    version.save()

    return json_success()

@json_login_required
@json_post_required
def ajax_upload_samples(request):
    version = get_obj_from_request(request.POST, 'version', ProjectVersion)

    if version is None:
        return json_failure(design.bad_version_id)

    band = version.project.band

    if not band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    files = request.FILES.getlist('file')

    for item in files:
        handle_sample_upload(item, request.user, band)
    band.save()
    
    return json_success()

def ajax_provide_project(request):
    version = get_obj_from_request(request.POST, 'version', ProjectVersion)

    if version is None:
        return json_failure(design.bad_version_id)

    band = version.project.band

    if not band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    project_handle = request.FILES.get('file')
    handle_project_upload(project_handle, request.user, version.song)

    return json_success()

@json_login_required
@json_post_required
def ajax_provide_mp3(request):
    version = get_obj_from_request(request.POST, 'version', ProjectVersion)

    if version is None:
        return json_failure(design.bad_version_id)

    band = version.project.band

    if not band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    mp3_handle = request.FILES.get('file')

    result = handle_mp3_upload(mp3_handle, version.song)
    if result['success']:
        version.song.save()
        return json_success()
    else:
        return json_failure(result['reason'])

@json_login_required
@json_post_required
def ajax_checkout(request):
    project = get_obj_from_request(request.POST, 'project', Project)

    if project is None:
        return json_failure(design.bad_project_id)

    # make sure user can work on this band
    if not project.band.permission_to_work(request.user):
        return json_failure(design.you_dont_have_permission_to_work_on_this_band)

    # make sure project is available
    if project.checked_out_to is not None:
        return json_failure(design.this_project_already_checked_out)

    project.checked_out_to = request.user
    project.save();

    return json_success()

@json_login_required
@json_post_required
def ajax_checkin(request):
    project = get_obj_from_request(request.POST, 'project', Project)
    
    if project is None:
        return json_failure(design.bad_project_id)

    # make sure project is checked out to request user
    if project.checked_out_to.id != request.user.id:
        return json_failure(design.not_checked_out_to_you)

    project_file = request.FILES.get('project_file')
    mp3_preview = request.FILES.get('mp3_preview')
    comments = request.POST.get('comments', '')

    if project_file is None and mp3_preview is None:
        # just check in
        project.checked_out_to = None
        project.save()
        return json_success()
    
    # must supply a project file
    if project_file is None:
        return json_failure(design.must_submit_project_file)

    new_version_number = project.latest_version.version + 1
    filename_appendix = "_" + str(new_version_number)

    # upload the song and make a new project version
    result = upload_song(request.user,
        file_mp3_handle=mp3_preview,
        file_source_handle=project_file,
        band=project.band,
        song_title=project.title,
        song_comments=comments,
        filename_appendix=filename_appendix)

    if not result['success']:
        return json_failure(result['reason'])

    song = result['song']
    song.save()

    # make a new version
    version = ProjectVersion()
    version.project = project
    version.song = song
    version.version = new_version_number
    version.saveNewVersion()

    # update project info
    project.checked_out_to = None
    project.latest_version = version
    project.title = song.title
    project.save()

    return json_success()

@login_required
def band_settings(request, band_id_str):
    band = get_object_or_404(Band, pk=int(band_id_str))

    if request.method == 'POST':
        form = RenameBandForm(request.POST)
        if form.is_valid():
            # rename the band
            new_name = form.cleaned_data.get('new_name')
            band.rename(new_name)
            band.save()

            return HttpResponseRedirect(reverse("workbench.band", args=[band.id]))
    else:
        form = RenameBandForm()

    return render_to_response('workbench/band_settings.html', locals(), context_instance=RequestContext(request))

@login_required
def band_settings_space(request, band_id_str):
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

            # upload the song
            result = upload_song(request.user,
                file_mp3_handle=mp3_file,
                file_source_handle=source_file, 
                band=band,
                song_title=form.cleaned_data.get('title'),
                song_comments=form.cleaned_data.get('comments', ''),
                filename_appendix="_1")
            if not result['success']:
                err_msg = result['reason']
            else:
                # fill in the rest of the fields
                song = result['song']
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

@login_required
def download_sample_zip(request):
    sample_id_strs = request.GET.getlist('s')
    
    sample_ids = []
    for sample_id_str in sample_id_strs:
        try:
            sample_id = int(sample_id_str)
        except ValueError:
            continue
        sample_ids.append(sample_id)

    samples = UploadedSample.objects.filter(pk__in=sample_ids)

    # authorize
    for sample in samples:
        if sample.user.id != request.user.id and not sample.band.permission_to_view_source(request.user):
            return HttpResponseForbidden()

    # package as zip
    zip_file_h = make_timed_temp_file()
    z = zipfile.ZipFile(zip_file_h, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)

    import storage

    def store_file_id(file_id, title):
        tmp = tempfile.NamedTemporaryFile(mode='r+b')
        storage.engine.retrieve(file_id, tmp.name)
        z.write(tmp.name, title)
        tmp.close()

    for sample in samples:
        file_id = sample.sample_file.path
        store_file_id(file_id, sample.title)

    z.close()
            
    response = HttpResponse(FileWrapper(zip_file_h), mimetype='application/zip')
    response['Content-Disposition'] = 'attachment; filename="samples.zip"'
    response['Content-Length'] = zip_file_h.tell()

    zip_file_h.seek(0)
    return response

@login_required
def download_sample(request, sample_id_str, sample_title):
    sample_id = int(sample_id_str)
    sample = get_object_or_404(UploadedSample, pk=sample_id)

    if sample.user.id != request.user.id and not sample.band.permission_to_view_source(request.user):
        # not authorized
        return HttpResponseForbidden()

    # grab the sample from storage to temp file
    import storage

    sample_file_h = make_timed_temp_file()
    storage.engine.retrieve(sample.sample_file.path, sample_file_h.name)

    # return to browser
    response = HttpResponse(FileWrapper(sample_file_h), mimetype='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename="%s"' % sample_title
    response['Content-Length'] = os.path.getsize(sample_file_h.name)

    sample_file_h.seek(0)
    return response
    
@json_login_required
@json_get_required
def download_zip(request):
    song = get_obj_from_request(request.GET, 'song', Song)

    if song is None:
        return json_failure(design.bad_song_id)

    if not song.permission_to_view_source(request.user):
        return json_failure(design.you_dont_have_permission_to_view_source)

    wanted_samples = request.GET.getlist('s')
    if len(wanted_samples) == 0:
        want_project = True
        deps = SampleDependency.objects.filter(song=song).exclude(uploaded_sample=None)
    else:
        want_project = False

        wanted_sample_ids = []
        
        for wanted_sample in wanted_samples:
            if wanted_sample == 'project':
                want_project = True
                continue
            try:
                wanted_sample_id = int(wanted_sample)
            except ValueError:
                continue

            wanted_sample_ids.append(wanted_sample_id)

        deps = SampleDependency.objects.filter(pk__in=wanted_sample_ids, song=song).exclude(uploaded_sample=None)

    zip_file_h = make_timed_temp_file()
    z = zipfile.ZipFile(zip_file_h, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)

    import storage

    def store_file_id(file_id, title):
        tmp = tempfile.NamedTemporaryFile(mode='r+b')
        storage.engine.retrieve(file_id, tmp.name)
        z.write(tmp.name, title)
        tmp.close()
        
    if want_project:
        path, title = os.path.split(song.source_file)
        store_file_id(song.source_file, title)

    for dep in deps:
        file_id = dep.uploaded_sample.sample_file.path
        store_file_id(file_id, dep.title)

    z.close()

    response = HttpResponse(FileWrapper(zip_file_h), mimetype='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % clean_filename(song.displayString() + '.zip')
    response['Content-Length'] = zip_file_h.tell()

    zip_file_h.seek(0)
    return response

def plugin(request, url):
    plugin = get_object_or_404(PluginDepenency, url=url)
    return render_to_response('workbench/plugin.html', locals(), context_instance=RequestContext(request))

def studio(request, identifier):
    studio = get_object_or_404(Studio, identifier=identifier)
    return render_to_response('workbench/studio.html', locals(), context_instance=RequestContext(request))

def song_to_dict(song, user):
    profile = user.get_profile()

    d = song.to_dict(access=SerializableModel.OWNER, chains=['owner', 'studio', 'comment_node'])
    if song.studio:
        d['studio']['logo_16x16'] = song.studio.logo_16x16.url
        d['studio']['missing'] = song.studio not in profile.studios.all()

    d['source_file'] = song.source_file

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
    
def version_to_dict(version, user):
    data = {
        'version': version.version,
        'new_title': version.new_title,
        'date_added': version.date_added,
        'id': version.id,
    }

    if version.song is not None:
        data['song'] = song_to_dict(version.song, user)
    else:
        data['song'] = None
        data['comment_node'] = version.comment_node.to_dict()
        data['owner'] = version.owner.get_profile().to_dict()

    if version.provided_samples.count() > 0:
        data['provided_samples'] = [x.to_dict(access=SerializableModel.OWNER, chains=['sample_file']) for x in version.provided_samples.all()]
    else:
        data['provided_samples'] = []

    return data

