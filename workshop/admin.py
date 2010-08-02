from django.contrib import admin
from workshop.models import ProjectVersion, Project, BandInvitation, Studio, \
    PluginDepenency, SampleDependency, UploadedSample, SampleFile, LogEntry

stuff = (
    ProjectVersion,
    Project,
    BandInvitation,
    Studio,
    PluginDepenency,
    SampleDependency,
    UploadedSample,
    SampleFile,
    LogEntry,
)

map(lambda x: admin.site.register(x), stuff)

