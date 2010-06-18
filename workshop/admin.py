from workshop.models import *
from django.contrib import admin

stuff = (
    ProjectVersion,
    Project,
    BandInvitation,
    Studio,
    PluginDepenency,
    SampleDependency,
    UploadedSample,
    SampleFile,
)

map(lambda x: admin.site.register(x), stuff)

