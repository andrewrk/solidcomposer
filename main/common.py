from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth.models import User

from datetime import datetime
import string
import random
import hashlib
import zipfile
import tempfile
import shutil
import simplejson as json

import main

import os

def gravatar_url(email, size):
    return "http://www.gravatar.com/avatar/%s?s=%s&r=pg&d=identicon" % (hashlib.md5(email).hexdigest(), str(size))

def file_hash(filename):
    md5 = hashlib.md5()
    f = open(filename, 'rb')
    md5.update(f.read())
    f.close()
    return md5.hexdigest()

def create_hash(length):
    """
    returns a string of length length with random alphanumeric characters
    """
    chars = string.letters + string.digits
    code = ""
    for i in range(length):
        code += chars[random.randint(0, len(chars)-1)]
    return code

def json_dthandler(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%B %d, %Y %H:%M:%S')
    else:
        return None

def json_dump(obj):
    return json.dumps(obj, default=json_dthandler)

def json_response(data):
    return HttpResponse(json_dump(data), mimetype="text/plain")

def json_success(data):
    return json_response({
        "success": True,
        "data": data,
    })

def json_post_required(function):
    "decorator that ensures request is via POST"

    def decorated(*args, **kwargs):
        request = args[0]
        if request.method == 'POST':
            return function(*args, **kwargs)
        else:
            return json_failure(main.design.must_submit_via_get)

    return decorated

def json_get_required(function):
    "decorator that ensures request is via GET"

    def decorated(*args, **kwargs):
        request = args[0]
        if request.method == 'GET':
            return function(*args, **kwargs)
        else:
            return json_failure(main.design.must_submit_via_get)

    return decorated

def json_login_required(function):
    "decorator that ensures ajax views are logged in."

    def decorated(*args, **kwargs):
        request = args[0]
        if request.user.is_authenticated():
            return function(*args, **kwargs)
        else:
            return json_response({
                'success': False,
                'reason': main.design.not_authenticated,
                'user': {'is_authenticated': False},
            })

    return decorated

def json_failure(reason):
    return json_response({
        "success": False,
        "reason": reason,
    })

def remove_unsafe_keys(hash, model):
    """
    look for UNSAFE_KEYS in the model. if it exists, delete all those entries
    from the hash.
    """
    if issubclass(model, User):
        check = (
            'password',
            'user_permissions',
            'is_user',
            'is_staff'
            'is_superuser',
            'email',
            'first_name',
            'last_name',
            'groups',
        )
    else:
        try:
            check = model.UNSAFE_KEYS
        except AttributeError:
            return

    for key in check:
        if hash.has_key(key):
            del hash[key]
        
def safe_model_to_dict(model_instance):
    hash = model_to_dict(model_instance)
    remove_unsafe_keys(hash, type(model_instance))
    if issubclass(type(model_instance), User):
        hash['get_profile'] = safe_model_to_dict(model_instance.get_profile())
    return hash

def zip_walk(zip_filename, callback):
    """
    unzip zip_filename to a temporary folder and execute
        callback(extracted_filename) on each one.
    returns the number of times callback was called.
        (0 means empty, -1 means error)
    there will be no leftover temp files when this function returns.
        (it cleans up after itself.)
        it will not delete zip_filename, however.
    """
    try:
        z = zipfile.ZipFile(zip_filename, 'r')
    except zipfile.BadZipfile:
        return -1

    # extract every file to a temp folder 
    tmpdir = tempfile.mkdtemp()
    z.extractall(path=tmpdir)
    extracted_files = superwalk(tmpdir)
    for extracted_file in extracted_files:
        callback(extracted_file)
        try:
            os.remove(extracted_file)
        except OSError:
            pass

    # clean up
    shutil.rmtree(tmpdir)
    return

def superwalk(folder):
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            yield os.path.join(dirpath, filename)

