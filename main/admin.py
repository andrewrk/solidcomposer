from django.contrib import admin
from main.models import Profile, AccountPlan, Song, SongCommentNode, Band, \
    BandMember, Tag, TempFile

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

