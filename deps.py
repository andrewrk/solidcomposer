# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

"""
this file checks to make sure python dependencies are installed.
it outpus a space separated list of missing dependencies.

 * python (the minimum version)
 * django - http://www.djangoproject.com/
 * south - http://south.aeracode.org/
   - A good database system like postgresql or mysql so that the migration
     stuff can work. (sqlite3 will not work)
 * psycopg2
 * simplejson
 * django extensions - http://code.google.com/p/django-command-extensions/
 * mutagen - http://code.google.com/p/mutagen/
 * PyWaveform - http://github.com/superjoe30/PyWaveform
 * PyDaw - http://github.com/superjoe30/PyDaw
 * django-storages - http://code.welldev.org/django-storages/wiki/S3Storage
 * boto - http://code.google.com/p/boto/
 * fpys - http://github.com/superjoe30/fpys
"""

deps = [
    'simplejson',
    'psycopg2',
    'python-2.6',
    'django-1.2.1',
    'south-0.7.1',
    'mutagen-1.19',
    'waveform-0.2',
    'PyDaw-0.4.5',
    'django_extensions-0.4.1',
    'boto',
    'django-storages',
    'fpys-0.5.1',
]

# python
import sys
if sys.version_info[:2] >= (2, 6):
    deps.remove('python-2.6')

# simplejson
try:
    import simplejson #@UnusedImport
    deps.remove('simplejson')
except ImportError:
    pass

# psycopg2
try:
    import psycopg2 #@UnusedImport
    deps.remove('psycopg2')
except ImportError:
    pass

# boto
try:
    import boto.s3 #@UnusedImport
    deps.remove('boto')
except ImportError:
    pass

# django-storages
try:
    import storages.backends.s3boto #@UnusedImport
    deps.remove('django-storages')
except ImportError:
    pass

# south
try:
    import south
    if south.__version__ == '0.7.1':
        deps.remove('south-0.7.1')
    else:
        sys.stderr.write("installed south version %s does not equal %s\n" % (south.__version__, '0.7.1'))
except ImportError:
    pass

# django
try:
    import django
    if django.get_version() == '1.2.1':
        deps.remove('django-1.2.1')
    else:
        sys.stderr.write("installed django version %s does not equal %s\n" % (django.get_version(), '1.2.1'))
except ImportError:
    pass

# mutagen
try:
    import mutagen
    if mutagen.version_string == '1.19':
        deps.remove('mutagen-1.19')
    else:
        sys.stderr.write("installed mutagen version %s does not equal %s\n" % (mutagen.version_string, '1.19'))
except ImportError:
    pass

# PyWaveform
try:
    import waveform
    if waveform.__version__ == '0.2':
        deps.remove('waveform-0.2')
    else:
        sys.stderr.write("installed waveform version %s does not equal %s\n" % (waveform.__version__, '0.2'))
except ImportError:
    pass

# PyDaw
try:
    import daw
    if daw.__version__ == '0.4.5':
        deps.remove('PyDaw-0.4.5')
    else:
        sys.stderr.write("installed PyDaw version %s does not equal %s\n" % (daw.__version__, '0.4.5'))
except ImportError:
    pass

# django extensions
try:
    import django_extensions
    if django_extensions.__version__:
        deps.remove('django_extensions-0.4.1')
    else:
        sys.stderr.write("installed django_extensions version %s does not equal %s\n" % (django_extensions.__version__, '0.4.1'))
except ImportError:
    pass

# fpys
try:
    import fpys
    if fpys.__version__ == '0.5.1':
        deps.remove('fpys-0.5.1')
    else:
        sys.stderr.write("installed fpys version %s does not equal %s\n" % (fpys.__version__, '0.5.1'))
except ImportError:
    pass

# output is a list of missing dependencies
if len(deps) > 0:
    print(" ".join(deps))

