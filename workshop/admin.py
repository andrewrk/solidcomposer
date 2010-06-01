from workshop.models import *
from django.contrib import admin

stuff = (
    ProjectVersion,
    Project,
    BandInvitation,
)

map(lambda x: admin.site.register(x), stuff)

