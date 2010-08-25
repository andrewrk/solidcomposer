#!/usr/bin/python

import os
import sys
import time

watchlist = {}
watched_extensions = ('.py')

def is_hidden(path):
    """
    Check if a file or folder is hidden.
    """
    _name, title = os.path.split(path)
    return title[-1] == '~' or title[0] == '.'

def examine_watchlist():
    """
    if any template files have changed since this function was last called,
    return True and update the list
    """
    global watchlist
    global watched_extensions

    new_item = False
    this_folder = os.path.abspath(os.path.dirname(__file__))
    for root, _dirs, files in os.walk(this_folder):
        # stay out of media!
        if '/media/' in root:
            continue
        for file in files:
            _prefix, ext = os.path.splitext(file)
            if ext not in watched_extensions:
                continue
            
            full_path = os.path.join(root, file)
            file_modified = os.path.getmtime(full_path)
            if watchlist.has_key(full_path):
                if file_modified > watchlist[full_path]:
                    new_item = True
            else:
                new_item = True
            watchlist[full_path] = file_modified

    return new_item

def restart_server():
    os.system("/etc/init.d/apache2 restart")

def main():
    """
    Watches for new or changed files and restarts the server if they are found.
    """
    while True:
        try:
            if examine_watchlist():
                restart_server()
        except KeyboardInterrupt:
            sys.exit(0)

        try:
            time.sleep(2)
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == '__main__':
    main()
