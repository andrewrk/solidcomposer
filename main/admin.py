from opensourcemusic.main.models import *
from django.contrib import admin

stuff = (
    Profile,
    Competition,
    ThumbsUp,
    Entry,
    Song,
    SongCommentThread,
    SongComment,
    ChatRoom,
    ChatMessage,
    Appearance,
)

map(lambda x: admin.site.register(x), stuff)

