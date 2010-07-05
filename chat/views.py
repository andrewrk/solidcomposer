from django.shortcuts import get_object_or_404
from chat.models import *
from main.common import *
from django.conf import settings

from datetime import datetime, timedelta

from chat import design

@json_get_required
def ajax_hear(request):
    """
    get new or all messages
    """
    last_message_str = request.GET.get('last_message', 'null')

    room = get_obj_from_request(request.GET, 'room', ChatRoom)
    if room is None:
        return json_failure(design.bad_room_id)

    # make sure user has permission to be in this room
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'permission_read': room.permission_to_hear(request.user),
            'permission_write': room.permission_to_chat(request.user),
        },
        'room': room.to_dict(),
        'messages': [],
        'success': True
    }

    if request.user.is_authenticated():
        data['user'].update({
            'username': request.user.username,
        })

    if data['user']['permission_read']:
        def add_to_message(msg):
            return {
                'id': msg.id,
                'type': msg.type,
                'author': {
                    'username': msg.author.username,
                    'id': msg.author.id,
                },
                'message': msg.message,
                'timestamp': msg.timestamp,
            }

        if last_message_str == 'null':
            # get entire log for this chat.
            data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room)]
        else:
            try:
                last_message_id = int(last_message_str)
            except ValueError:
                last_message_id = 0

            data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room, id__gt=last_message_id)]

    if data['user']['permission_write']:
        # mark an appearance in the ChatRoom
        if request.user.is_authenticated() and room.is_active():
            appearances = Appearance.objects.filter(person=request.user, room=room)
            if appearances.count() > 0:
                appearances[0].save() # update the timestamp
            else:
                new_appearance = Appearance()
                new_appearance.room = room
                new_appearance.person = request.user
                new_appearance.save()

                # join message
                m = ChatMessage()
                m.room=room
                m.type=JOIN
                m.author=request.user
                m.save()

    return json_response(data)

@json_login_required
@json_post_required
def ajax_say(request):
    room = get_obj_from_request(request.POST, 'room', ChatRoom)
    if room is None:
        return json_failure(design.bad_room_id)

    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'permission_read': room.permission_to_hear(request.user),
            'permission_write': room.permission_to_chat(request.user),
        },
        'success': False,
    }

    if not room.is_active():
        return json_failure(design.room_is_not_active)

    message = request.POST.get('message', '')

    if message == "":
        return json_failure(design.cannot_say_blank_message)

    if not data['user']['permission_write']:
        return json_failure(design.you_lack_write_permission)

    # we're clear. add the message
    m = ChatMessage()
    m.room = room
    m.type = MESSAGE
    m.author = request.user
    m.message = message
    m.save()

    data['success'] = True
    return json_response(data)

@json_get_required
def ajax_onliners(request):
    room = get_obj_from_request(request.GET, 'room', ChatRoom)
    if room is None:
        return json_failure(design.bad_room_id)

    if not room.is_active():
        return json_failure(design.room_is_not_active)

    expire_date = datetime.now() - timedelta(seconds=settings.CHAT_TIMEOUT)
    data = [x.person.get_profile().to_dict() for x in Appearance.objects.filter(room=room, timestamp__gt=expire_date)]
    return json_success(data)
