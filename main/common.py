from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth.models import User

from datetime import datetime
import string
import random
import simplejson as json

from main import design

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
            return json_failure(design.must_submit_via_get)

    return decorated

def json_get_required(function):
    "decorator that ensures request is via GET"

    def decorated(*args, **kwargs):
        request = args[0]
        if request.method == 'GET':
            return function(*args, **kwargs)
        else:
            return json_failure(design.must_submit_via_get)

    return decorated

def json_login_required(function):
    "decorator that ensures ajax views are logged in."

    def decorated(*args, **kwargs):
        request = args[0]
        if request.user.is_authenticated():
            return function(*args, **kwargs)
        else:
            return json_failure(design.not_authenticated)

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
    
