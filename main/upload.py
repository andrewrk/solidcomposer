import os
import stat
import string

def upload_file(f, new_name):
    handle = open(new_name, 'wb+')
    upload_file_h(f, handle)
    handle.close()
    os.chmod(new_name, stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)

def upload_file_h(f, handle):
    for chunk in f.chunks():
        handle.write(chunk)

def safe_file(path, title):
    """
    returns a tuple (title joined with path, only title). paths are guaranteed
    to be unique and safe.
    """
    allowed = string.letters + string.digits + "_-."
    clean = ""
    for c in title:
        if c in allowed:
            clean += c
        else:
            clean += "_"

    # break into title and extension
    parts = clean.split(".")
    if len(parts) > 0:
        clean = ".".join(parts[:-1])
        ext = "." + parts[-1]
    else:
        ext = ""
    
    if os.path.exists(os.path.join(path, clean + ext)):
        # use digits
        suffix = 2
        while os.path.exists(os.path.join(path, clean + str(suffix) + ext)):
            suffix += 1
        unique = clean + str(suffix) + ext
    else:
        unique = clean + ext

    return (os.path.join(path,unique), unique)

