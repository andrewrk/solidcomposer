from django.contrib import admin
from main.models import *

stuff = (
    Profile,
    AccountPlan,
    Song,
    SongCommentNode,
    Band,
    BandMember,
    Tag,
    TempFile,
    Transaction,
)

map(lambda x: admin.site.register(x), stuff)

