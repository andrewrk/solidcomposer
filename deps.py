import os
import sys

"""
this file checks to make sure python dependencies are installed.
it outpus a space separated list of missing dependencies.

 * django - http://www.djangoproject.com/
 * south - http://south.aeracode.org/
   - A good database system like postgresql or mysql so that the migration
     stuff can work. (sqlite3 will not work)
 * django extensions - http://code.google.com/p/django-command-extensions/
 * mutagen - http://code.google.com/p/mutagen/
 * PyWaveform - http://github.com/superjoe30/PyWaveform
 * PyFlp - http://github.com/superjoe30/PyFlp

"""

deps = [
    'django-1.2.1',
    'south-0.7.1',
    'mutagen-1.15',
    'waveform',
    'flp',
    'django_extensions-0.4.1',
]

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
    if mutagen.version_string == '1.15':
        deps.remove('mutagen-1.15')
    else:
        sys.stderr.write("installed mutagen version %s does not equal %s\n" % (mutagen.version_string, '1.15'))
except ImportError:
    pass

# PyWaveform
try:
    import waveform
    deps.remove('waveform')
except ImportError:
    pass

# PyFlp
try:
    import flp
    deps.remove('flp')
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

# output is a list of missing dependencies
if len(deps) > 0:
    print(" ".join(deps))

