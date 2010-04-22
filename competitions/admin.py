from opensourcemusic.competitions.models import *
from django.contrib import admin

stuff = (
    Competition,
    Entry,
    EntryCommentThread,
    EntryComment,
    ThumbsUp,
)

map(lambda x: admin.site.register(x), stuff)

