from opensourcemusic.chat.models import *
from django.contrib import admin

stuff = (
    ChatRoom,
    ChatMessage,
    Appearance,
)

map(lambda x: admin.site.register(x), stuff)

