from opensourcemusic.workshop.models import *
from opensourcemusic.main.models import *
from opensourcemusic.main.views import safe_model_to_dict, json_response
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render_to_response, get_object_or_404

def ajax_home(request):
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
    }

    if request.user.is_authenticated():
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

@login_required
def ajax_accept_invite(request):
    return handle_invite(request, accept=True)
    
@login_required
def ajax_ignore_invite(request):
    return handle_invite(request, accept=False)

def band(request):
    "todo"
    pass

def create_band(request):
    "todo"
    pass

