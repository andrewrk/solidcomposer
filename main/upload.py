import os
import stat
import string
import tempfile

def move_to_storage(full_path, file_key):
    """
    moves file at full_path to storage with key file_key
    """
    import storage
    storage.engine.store(full_path, file_key)
    os.remove(full_path)

def upload_file(f, filename):
    """
    uses the storage engine to store uploaded file f with key filename
    """
    # pick a nice temp file
    import storage
    tmp_h = tempfile.NamedTemporaryFile(delete=False)
    upload_file_h(f, tmp_h)
    tmp_h.close()
    storage.engine.store(tmp_h.name, filename)
    os.remove(tmp_h.name)

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

