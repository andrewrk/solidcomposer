from chat.models import ChatRoom, ChatMessage, Appearance
from django.contrib import admin

stuff = (
    ChatRoom,
    ChatMessage,
    Appearance,
)

map(lambda x: admin.site.register(x), stuff)
