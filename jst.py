#!/usr/bin/python

import os
import sys

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.template import Template

def print_usage():
    """
    display the help message to the user
    """
    print("""
Usage:

To compile:
%(program) compile

To clean:
%(program) clean
""" % {'program': sys.argv[0]})

def walk(compile_func):
    """
    for each source file, call compile_func with these arguments:
        source file absolute path
        dest file absolute path
    """
    for root, dirs, files in os.walk(settings.JST_DIR, followlinks=True):
        relative = root.replace(settings.JST_DIR, "")
        if relative[0] == os.sep:
            relative = relative[1:]

        for file in files:
            in_file = os.join(root, file)
            out_file = os.path.join(os.path.join(settings.JST_OUTPUT, relative), file)
            compile_func(in_file, out_file)

def compile_file(source, dest):
    file = open(dest, 'w')
    template = Template(open(source, 'r').read())
    file.write(template.render())
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
        funcs(sys.argv[1])


