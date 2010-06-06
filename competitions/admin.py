from competitions.models import *
from django.contrib import admin

stuff = (
    Competition,
    ThumbsUp,
    Entry,
)

map(lambda x: admin.site.register(x), stuff)

