from opensourcemusic.main.models import *
from django.contrib import admin

stuff = (
    Profile,
)

map(lambda x: admin.site.register(x), stuff)

