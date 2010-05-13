from django.shortcuts import get_object_or_404
from opensourcemusic import settings
from opensourcemusic.chat.models import *
from opensourcemusic.main.views import safe_model_to_dict, json_response

from datetime import datetime, timedelta

def user_can_chat(room, user):
    if room.permission_type == OPEN:
        return True
    else:
        # user has to be signed in
        if not user.is_authenticated():
            return False

        if room.permission_type == WHITELIST:
            # user has to be on the whitelist
            if room.whitelist.filter(pk=user.id).count() != 1:
                return False
        elif room.permission_type == BLACKLIST:
            # user is blocked if he is on the blacklist 
            if room.blacklist.filter(pk=user.id).count() == 1:
                return False

        return True

def ajax_hear(request):
    """
    get new or all messages
    """
    last_message_str = request.GET.get('last_message', 'null')
    room_id = request.GET.get('room', 0)
    try:
        room_id = int(room_id)
    except:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    # make sure user has permission to be in this room
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'has_permission': False,
        },
        'room': safe_model_to_dict(room),
        'messages': [],
    }

    if request.user.is_authenticated():
        data['user']['get_profile'] = safe_model_to_dict(request.user.get_profile())
        data['user']['username'] = request.user.username

    data['user']['has_permission'] = user_can_chat(room, request.user)

    def add_to_message(msg):
        d = safe_model_to_dict(msg)
        d['author'] = safe_model_to_dict(msg.author)
        d['timestamp'] = msg.timestamp
        return d

    if last_message_str == 'null':
        # get entire log for this chat.
        data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room).order_by('timestamp')]
    else:
        try:
            last_message_id = int(last_message_str)
        except:
            last_message_id = 0

        last_message = get_object_or_404(ChatMessage, id=last_message_id)
        data['messages'] = [add_to_message(x) for x in ChatMessage.objects.filter(room=room, id__gt=last_message_id).order_by('timestamp')]

    if request.user.is_authenticated():
        # mark an appearance in the ChatRoom
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
    except:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    if not chatroom_is_active(room):
        return json_response({})

    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
            'has_permission': False,
        },
    }

    message = request.POST.get('message', '')

    if message == "" or not request.user.is_authenticated():
        return json_response(data)

    data['user']['has_permission'] = user_can_chat(room, request.user)
    if not data['user']['has_permission']:
        return json_response(data)

    # we're clear. add the message
    m = ChatMessage()
    m.room = room
    m.type = MESSAGE
    m.author = request.user
    m.message = message
    m.save()

    return json_response(data)

def chatroom_is_active(room):
    now = datetime.now()
    if not room.start_date is None:
        if room.start_date > now:
            return False
    if not room.end_date is None:
        if room.end_date < now:
            return False
    return True

def ajax_onliners(request):
    room_id = request.GET.get('room', 0)
    try:
        room_id = int(room_id)
    except:
        room_id = 0
    room = get_object_or_404(ChatRoom, id=room_id)

    if not chatroom_is_active(room):
        return json_response({})

    expire_date = datetime.now() - timedelta(seconds=settings.CHAT_TIMEOUT)
    data = [x.person.username for x in Appearance.objects.filter(room=room, timestamp__gt=expire_date)]

    return json_response(data)

