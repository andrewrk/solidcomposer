from django.core.urlresolvers import reverse
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

@json_login_required
def ajax_home(request):
    data = {}

    data['user'] = safe_model_to_dict(request.user)

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
    if band_id == 0:
        return json_failure("bad band id")
    projects = Project.objects.filter(band__pk=band_id)
    visible = projects.filter(visible=True)
    scrapped = projects.filter(visible=False)
    results = [
        ("all", "All", visible.count()),
        ("available", "Available", visible.filter(checked_out_to=None).count()),
        ("out", "Checked out", visible.exclude(checked_out_to=None).count()),
        ("mine", "Checked out to me", visible.filter(checked_out_to=request.user).count()),
        ("scrapped", "Scrapped", scrapped.count()),
    ] 
    return json_success(results)

@json_login_required
@json_get_required
def ajax_project(request):
    """
    return the project history. if a last_version is supplied, only
    return newer ones. Also return the current state - who has it
    checked out, etc.
    """


    return json_response({})

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
                result = upload_song(
                    file_mp3_handle=mp3_file,
                    file_source_handle=source_file, 
                    band=band,
                    song_title=form.cleaned_data.get('title'))
                if not result['success']:
                    err_msg = result['reason']
                else:
                    # fill in the rest of the fields
                    song = result['song']
                    song.owner = request.user
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
                    version.save()

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
    
