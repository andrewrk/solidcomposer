import sys
import os
import re
import subprocess

"""
stdin - the output of ./manage.py migrate --list
        from the server

this script is responsible for
resetting the client database and
migrating to the server's state.
"""
import settings

def get_state(migrate_output_text):
    expect_name = True
    exp = re.compile(r'^\s+\(([* ])\)\s+(\d{4})')
    state = {} # maps app_name to migration number
    for line in migrate_output_text.split("\n"):
        if line.strip() == '':
            expect_name = True
            continue
        if expect_name:
            expect_name = False
            app_name = line.strip()
            continue

        m = exp.match(line)
        if m is not None:
            migrated = bool(m.group(1) == '*')
            number = m.group(2)

            if migrated:
                state[app_name] = number

            continue

        print("Error: unexpected line:\n%s\n" % line)
        sys.exit(1)

    return state

# reset the client database
def system(command):
    "run a command on the system"
    print(command)
    p = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    out = p.communicate()[0].strip()
    code = p.returncode
    if code:
        sys.exit(code)
    else:
        return out

def get_apps():
    prefix = 'opensourcemusic.'
    apps = map(lambda x: x[len(prefix):], filter(lambda x: x[:len(prefix)] == prefix, settings.INSTALLED_APPS))
    return apps

# parse input
state = get_state(sys.stdin.read())

# get list of apps used
apps = " ".join(get_apps())

# reset the database
if settings.DATABASE_ENGINE == 'postgresql_psycopg2': 
    cmd = 'echo "DROP DATABASE %s; CREATE DATABASE %s;" | psql template1' % (settings.DATABASE_NAME, settings.DATABASE_NAME)
    print(cmd)
    code = os.system(cmd)
    if code:
        sys.exit(code)
else:
    system("python manage.py reset --noinput %s" % apps)

system("python manage.py syncdb --noinput")

# migrate to the server's state
for app, number in state.iteritems():
    system("python manage.py migrate %s %s" % (app, number))
