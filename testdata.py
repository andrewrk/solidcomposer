#!/usr/bin/python

import os
import sys

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

def print_usage():
    """
    display the help message to the user
    """
    if len(sys.argv) >= 3 and sys.argv[1].lower() == 'help' and commands.has_key(sys.argv[2]):
        # print doc string for method
        args = {
            'doc': commands[sys.argv[2]].__doc__,
            'program': sys.argv[0],
            'key': sys.argv[2],
        }
        print("""
Usage for %(key)s:

%(program)s %(key)s

%(doc)s
""" % args)
    else:
        sorted_keys = commands.keys()
        sorted_keys.sort()
        args = {
            'program': sys.argv[0],
            'commands': "\n".join(sorted_keys),
        }

        print("""Usage:

%(program)s <command>

Where <command> is:
%(commands)s

For extra help, type:
%(program)s help <command>
""" % args)

def load_data():
    # reset the database
    if os.path.exists(settings.DATABASE_NAME):
        os.remove(settings.DATABASE_NAME)

    # syncdb
    os.system("./manage.py syncdb --noinput")
    os.system("./manage.py reset auth --noinput")

    # load dump
    os.system("./manage.py loaddata dump.json")
    
def save_data():
    os.system("./manage.py dumpdata --exclude=contenttypes >dump.json")

commands = {
    'help': print_usage,
    'save': save_data,
    'load': load_data,
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or not commands.has_key(sys.argv[1]):
        print_usage();
        sys.exit(1)
    else:
        commands[sys.argv[1]]()

