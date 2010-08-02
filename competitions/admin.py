from competitions.models import Competition, ThumbsUp, Entry
from django.contrib import admin

stuff = (
    Competition,
    ThumbsUp,
    Entry,
)

map(lambda x: admin.site.register(x), stuff)

