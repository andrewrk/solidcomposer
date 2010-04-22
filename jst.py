#!/usr/bin/python

import os
import sys

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.template import Template, Context
from django.template.loader import *

def print_usage():
    """
    display the help message to the user
    """
    print("""Usage:

To compile:
%(program)s compile

To clean:
%(program)s clean
""" % {'program': sys.argv[0]})

def is_hidden(path):
    """
    Check if a file or folder is hidden.
    """
    title = file_title(path)
    return title[-1] == '~' or title[0] == '.'

def file_title(path):
    """
    Get only the title of a path.
    """
    names = path.split(os.sep)
    if len(names) == 0:
        return path
    else:
        return names[-1]

def walk(compile_func):
    """
    for each source file, call compile_func with these arguments:
        source file absolute path
        dest file absolute path
    """
    for root, dirs, files in os.walk(settings.JST_DIR, followlinks=True):
        relative = root.replace(settings.JST_DIR, "")
        if len(relative) > 0 and relative[0] == os.sep:
            relative = relative[1:]

        for file in files:
            in_file = os.path.join(root, file)
            if not is_hidden(in_file):
                out_file = os.path.join(settings.JST_OUTPUT, relative, file)
                compile_func(in_file, out_file)

def compile_file(source, dest):
    file = open(dest, 'w')
    in_text = open(source, 'r').read().decode()
    template = Template(in_text)
    file.write(template.render(Context()))
    file.close()

def clean_file(source, dest):
    os.remove(dest)

def compile():
    """
    compile every file, mirroring directory structure
    """
    walk(compile_file)

def clean():
    """
    delete auto-generated files
    """
    walk(clean_file)

if __name__ == '__main__':
    funcs = {
        'compile': compile,
        'clean': clean,
    }
    if len(sys.argv) < 2 or not funcs.has_key(sys.argv[1]):
        print_usage();
        sys.exit(1)
    else:
        funcs[sys.argv[1]]()


