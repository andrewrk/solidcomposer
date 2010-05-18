import os

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
    'django',
    'south',
    'mutagen',
    'waveform',
    'flp',
    'django_extensions',
]

# south
try:
    import south
    deps.remove('south')
except ImportError:
    pass

# django
try:
    import django
    deps.remove('django')
except ImportError:
    pass

# mutagen
try:
    import mutagen
    deps.remove('mutagen')
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
    deps.remove('django_extensions')
except ImportError:
    pass

# output is a list of missing dependencies
if len(deps) > 0:
    print(" ".join(deps))

