import sys
import os

import settings

"""
this script is responsible for resetting the client database.
"""

def system(command):
    "run a command on the system"
    print(command)
    code = os.system(command)
    if code:
        sys.exit(code)

if settings.DATABASE_ENGINE == 'postgresql_psycopg2': 
    cmd = 'echo "DROP DATABASE %s; CREATE DATABASE %s;" | psql template1' % (settings.DATABASES['default']['NAME'], settings.DATABASES['default']['NAME'])
    system(cmd)
else:
    system("python manage.py reset --noinput %s" % apps)

#system("cd %s; python manage.py syncdb --noinput" % old)

# migrate to the server's state
#system("cd %s; python manage.py migrate" % old)
#for app, number in state.iteritems():
#    system("cd %s; python manage.py migrate %s %s" % (app, number))

