from django.shortcuts import get_object_or_404
from opensourcemusic import settings
from opensourcemusic.chat.models import *
from opensourcemusic.main.views import safe_model_to_dict, json_response

from datetime import datetime, timedelta

def ajax_hear(request):
    """
    get new or all messages
    """
    last_message_str = request.GET.get('last_message', 'null')
    room_id = request.GET.get('room', 0)
    try:
        room_id = int(room_id)
    except ValueError:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    # make sure user has permission to be in this room
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'has_permission': room.permission_to_chat(request.user),
        },
        'room': safe_model_to_dict(room),
        'messages': [],
    }

    if request.user.is_authenticated():
        data['user']['get_profile'] = safe_model_to_dict(request.user.get_profile())
        data['user']['username'] = request.user.username

    def add_to_message(msg):
        d = safe_model_to_dict(msg)
        d['author'] = {
            'username': msg.author.username,
            'id': msg.author.id,
        }
        d['timestamp'] = msg.timestamp
        return d

    if last_message_str == 'null':
        # get entire log for this chat.
        data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room)]
    else:
        try:
            last_message_id = int(last_message_str)
        except ValueError:
            last_message_id = 0

        last_message = get_object_or_404(ChatMessage, id=last_message_id)
        data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room, id__gt=last_message_id)]

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

def ajax_say(request):
    room_id = request.POST.get('room', 0)
    try:
        room_id = int(room_id)
    except ValueError:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'has_permission': False,
        },
        'success': False,
    }

    if not room.is_active():
        return json_response(data)

    message = request.POST.get('message', '')

    if message == "" or not request.user.is_authenticated():
        return json_response(data)

    data['user']['has_permission'] = room.permission_to_chat(request.user)
    if not data['user']['has_permission']:
        return json_response(data)

    # we're clear. add the message
    m = ChatMessage()
    m.room = room
    m.type = MESSAGE
    m.author = request.user
    m.message = message
    m.save()

    data['success'] = True
    return json_response(data)

def ajax_onliners(request):
    room_id = request.GET.get('room', 0)
    try:
        room_id = int(room_id)
    except ValueError:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    data = {}

    if not room.is_active():
        return json_response(data)

    expire_date = datetime.now() - timedelta(seconds=settings.CHAT_TIMEOUT)
    def person_data(x):
        d = safe_model_to_dict(x)
        d['get_profile']['get_points'] = x.get_profile().get_points()
        return d
    data = [person_data(x.person) for x in Appearance.objects.filter(room=room, timestamp__gt=expire_date)]
    return json_response(data)
