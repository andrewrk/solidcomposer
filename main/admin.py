from main.models import *
from django.contrib import admin

stuff = (
    Profile,
    AccountPlan,
    Song,
    SongCommentNode,
    Band,
    BandMember,
    Tag,
    TempFile,
)

map(lambda x: admin.site.register(x), stuff)

