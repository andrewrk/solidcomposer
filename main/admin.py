from main.models import *
from django.contrib import admin

stuff = (
    Profile,
    AccountPlan,
    Song,
    SongCommentThread,
    SongComment,
    Band,
    BandMember,
    Tag,
)

map(lambda x: admin.site.register(x), stuff)

