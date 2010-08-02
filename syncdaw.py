#!/usr/bin/python

"""
synchronizes the database with the capabilities of PyDaw
"""

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from workshop.models import Studio
import daw

for id in daw.ids():
    studios = Studio.objects.filter(identifier=id)
    assert studios.count() < 2
    if studios.count() == 0:
        # add the studio
        studio = Studio()
        studio.title = id
        studio.identifier = id
        print("Adding %s" % id)
    else:
        # update the studio
        studio = studios[0]

    d = daw.dawForId(id)
    studio.canReadFile = d.canReadFile
    studio.canMerge = d.canMerge
    studio.canRender = d.canRender

    studio.save()

