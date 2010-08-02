#!/usr/bin/python

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.template import Template, Context
import os
import storage
import sys
import tempfile
import time
import traceback


"""
Requires some things in your settings.py file:

# a tuple of tuples.
# (folder to watch, folder to output to, command to run),
# command to run is optional. Use None if you just want to copy the output.
# if you want another command to run, use %(in)s and %(out)s for the input and output files. 
PREPARSE_CHAIN = (
    (absolute(os.path.join('templates', 'preparsed')), absolute(os.path.join('media', 'js', 'pre')), None),
    (absolute(os.path.join('templates', 'pre', 'css')), absolute(os.path.join('media', 'css', 'pre')), "lessc %(in)s %(out)s"),
)

# the dictionary that will be available to your preparsed code.
PREPARSE_CONTEXT_MODULE = 'some_module'

# in that module, have e.g.:
from django.conf import settings
CONTEXT = {
    'MEDIA_URL': settings.MEDIA_URL,
}

# the reason it's in a different module is to avoid making settings.py dependent on other modules.
"""

context = Context(__import__(settings.PREPARSE_CONTEXT_MODULE).CONTEXT)

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

def is_hidden(path):
    """
    Check if a file or folder is hidden.
    """
    _name, title = os.path.split(path)
    return title[-1] == '~' or title[0] == '.'

def walk(compile_func):
    """
    for each source file, call compile_func with these arguments:
        source file absolute path
        dest file absolute path
    """
    for i in range(len(settings.PREPARSE_CHAIN)):
        in_folder, out_folder, out_ext, _cmd = settings.PREPARSE_CHAIN[i]
        if examine_watchlist(i):
            for root, _dirs, files in os.walk(in_folder, followlinks=True):
                relative = root.replace(in_folder, "")
                if len(relative) > 0 and relative[0] == os.sep:
                    relative = relative[1:]

                for file in files:
                    in_file = os.path.join(root, file)
                    if not is_hidden(in_file):
                        out_file_prefix, _out_file_old_ext = os.path.splitext(file)
                        new_filename = out_file_prefix + out_ext
                        out_file = os.path.join(out_folder, relative, new_filename)
                        compile_func(settings.PREPARSE_CHAIN[i], in_file, out_file)

watchlist = [{} for x in settings.PREPARSE_CHAIN]
ignored_extensions = (
    '.swp',
)
def examine_watchlist(chain_index):
    """
    if any template files have changed since this function was last called,
    return True and update the list
    """
    new_item = False
    in_folder, _out_folder, _out_ext, _cmd = settings.PREPARSE_CHAIN[chain_index]
    watch_folders = settings.TEMPLATE_DIRS + (in_folder,)
    watch_folders = set([os.path.abspath(folder) for folder in watch_folders])
    for template_dir in watch_folders:
        for root, _dirs, files in os.walk(template_dir):
            for file in files:
                _prefix, ext = os.path.splitext(file)
                if ext in ignored_extensions:
                    continue
                
                full_path = os.path.join(root, file)
                file_modified = os.path.getmtime(full_path)
                if watchlist[chain_index].has_key(full_path):
                    if file_modified > watchlist[chain_index][full_path]:
                        new_item = True
                else:
                    new_item = True
                watchlist[chain_index][full_path] = file_modified

    return new_item

def compile_file(preparse_tuple, source, dest):
    """
    parse source and write to dest
    """
    _in_folder, _out_folder, out_ext, cmd = preparse_tuple
    _source_path, source_title = os.path.split(source)
    _prefix, ext = os.path.splitext(source_title)
    print("Parsing %s." % source_title)

    in_text = open(source, 'r').read().decode()
    template = Template(in_text)

    f = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    f.write(template.render(context))
    f.close()

    if cmd is not None:
        f2 = tempfile.NamedTemporaryFile(suffix=out_ext, mode='r+b', delete=False)
        f2.close()

        cmd_str = cmd % {'in': f.name, 'out': f2.name}
        print(cmd_str)
        os.system(cmd_str)

        os.remove(f.name)
        store_name = f2.name
    else:
        store_name = f.name

    storage.engine.store(store_name, dest, reducedRedundancy=True)
    os.remove(store_name)

def clean_file(preparse_tuple, source, dest, force):
    if os.path.exists(dest):
        print("removing %s" % dest)
        os.remove(dest)

def parse():
    """
    parse every file, mirroring directory structure
    """
    walk(compile_file)

def clean():
    """
    delete auto-generated files
    """
    walk(clean_file)

def monitor():
    """
    Watches for new or changed files that are candidates for being preparsed,
    and automatically re-parses them.
    """
    while True:
        try:
            parse()
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            traceback.print_exc(file=sys.stdout)
        try:
            time.sleep(0.5)
        except KeyboardInterrupt:
            sys.exit(0)

commands = {
    'help': print_usage,
    'parse': parse,
    'clean': clean,
    'monitor': monitor,
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or not commands.has_key(sys.argv[1]):
        print_usage()
        sys.exit(1)
    else:
        commands[sys.argv[1]]()
