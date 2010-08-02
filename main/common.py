from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives

from datetime import datetime
import string
import random
import hashlib
import zipfile
import tempfile
import shutil
import simplejson as json

import main
from main.models import TempFile

import os

from django.conf import settings

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
    for _ in range(length):
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

def json_success(data=None):
    out_data = {'success': True}
    if data is not None:
        out_data['data'] = data
    return json_response(out_data)

def json_post_required(function):
    "decorator that ensures request is via POST"

    def decorated(*args, **kwargs):
        request = args[0]
        if request.method == 'POST':
            return function(*args, **kwargs)
        else:
            return json_failure(main.design.must_submit_via_post)

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
    for dirpath, _dirnames, filenames in os.walk(folder):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def make_timed_temp_file():
    handle = tempfile.NamedTemporaryFile(mode='rw+b', delete=False)

    tmp_file = TempFile()
    tmp_file.path = handle.name
    tmp_file.save()

    return handle

def get_type(post_data, name, default, type_obj):
    str_obj = post_data.get(name, default)
    try:
        typed_obj = type_obj(str_obj)
    except ValueError:
        typed_obj = default

    return typed_obj

def get_val(post_data, name, default):
    return get_type(post_data, name, default, type(default))

def get_obj_from_request(post_data, name, ObjectType):
    obj_id = get_val(post_data, name, 0)
    try:
        obj = ObjectType.objects.get(pk=obj_id)
    except ObjectType.DoesNotExist:
        obj = None
    return obj

def send_html_mail(subject, message_txt, message_html, to_list):
    msg = EmailMultiAlternatives(subject, message_txt, settings.DEFAULT_FROM_EMAIL, to_list)
    msg.attach_alternative(message_html, 'text/html')
    msg.send(fail_silently=True)

