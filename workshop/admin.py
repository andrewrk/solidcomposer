from workshop.models import *
from django.contrib import admin

stuff = (
    ProjectVersion,
    Project,
    BandInvitation,
    Studio,
    GeneratorDependency,
    SampleDependency,
    EffectDependency,
)

map(lambda x: admin.site.register(x), stuff)

