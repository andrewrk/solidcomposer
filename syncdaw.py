#!/usr/bin/python

"""
synchronizes the database with the capabilities of PyDaw
"""

logging = True

def log(line):
    if logging:
        print(line)

def syncdaw():
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
            log("Adding {0}".format(id))
        else:
            # update the studio
            studio = studios[0]
            log("Updating {0}".format(studio.title))

        d = daw.dawForId(id)
        studio.canReadFile = d.canReadFile
        studio.canMerge = d.canMerge
        studio.canRender = d.canRender

        studio.save()

if __name__ == '__main__':
    # set django environment
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)

    syncdaw()
