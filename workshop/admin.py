from opensourcemusic.workshop.models import *
from django.contrib import admin

stuff = (
    ProjectVersion,
    Project,
)

map(lambda x: admin.site.register(x), stuff)

