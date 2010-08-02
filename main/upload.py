import os
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

def clean_filename(title):
    """
    returns title except now it's safe to use as a filename
    """
    allowed = string.letters + string.digits + "_-."
    clean = ""
    for c in title:
        if c in allowed:
            clean += c
        else:
            clean += "_"
    return clean
    
