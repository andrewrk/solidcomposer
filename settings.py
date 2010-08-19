# Django settings for project.
# you can override any of this with settings_user.py, which does not get
# committed to source control.

import os

def absolute(relative_path):
    "make a relative path absolute"
    return os.path.normpath(os.path.join(os.path.dirname(__file__), relative_path))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
# set this to True to actually use the amazon services 
USE_AWS = False

ADMINS = (
    ('Andy Kelley', 'superjoe30@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'NAME': 'solidcomposer',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'dev',
        'PASSWORD': 'dev',
    },
}

# South
SOUTH_LOGGING_ON = False
SOUTH_LOGGING_FILE = absolute("south.log")
SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

TIME_ZONE = None # system time zone

LANGUAGE_CODE = 'en-us'
USE_I18N = False

# amazon s3 details
AWS_ACCESS_KEY_ID = 'xxxxxxxxxxxxxxxxxxxx'
AWS_SECRET_ACCESS_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
AWS_STORAGE_BUCKET_NAME = 'solidcomposer-test'
AWS_TEST_STORAGE_BUCKET_NAME = 'solidcomposer-test'
# copy and uncomment in settings_user.py to use s3 storage
#DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# make sure DEBUG is set to the value you want and run ./setup_amazon_payments.py to get these values.
AWS_RECIPIENT_INSTRUCTION_TOKEN_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AWS_RECIPIENT_INSTRUCTION_REQUEST_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AWS_CALLER_INSTRUCTION_TOKEN_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AWS_CALLER_INSTRUCTION_REQUEST_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

DEFAULT_FROM_EMAIL = 'admin@solidcomposer.com'
MEDIA_ROOT = absolute('media')
MEDIA_URL = 'http://localhost:8080/django/solidcomposer/'
ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '2_l-92-j(^)a=vsynmsw1d(efi!w@w#j#v@ucv^2i7cfsk=!8='

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'base.SSLMiddleware.SSLRedirect',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    absolute('templates'),
)

INTERNAL_IPS = (
    '127.0.0.1',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'south',
    'django_extensions',
    'main',
    'competitions',
    'chat',
    'workshop',
)

SITE_ID = 1

LOGIN_URL = "/login/"
AUTH_PROFILE_MODULE = 'main.Profile'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

# how many seconds to wait before generating leave messages for chatters
CHAT_TIMEOUT = 60

# maximum length of competition tracks in seconds
COMPO_ENTRY_MAX_LEN = 10 * 60

# minimum amount of time to give users for a competition in minutes
MINIMUM_COMPO_LENGTH = 10

# how many seconds to wait between tracks in listening party for buffering
LISTENING_PARTY_BUFFER_TIME = 10

# how many bytes to limit uploads to
FILE_UPLOAD_SIZE_CAP = 1024 * 1024 * 20  # 20 MB

# for pagination
ITEMS_PER_PAGE = 5

# how long does a user have to activate before it expires
ACTIVATION_EXPIRE_DAYS = 1

# free acount info
# how much disk space do bands get for freeeee
BAND_INIT_SPACE = 1024 * 1024 * 1024 * 0.5 # 0.5 GB
# how many bands can free users create
FREE_BAND_LIMIT = 10

URL_DISALLOWED_CHARS = r'\./?'

# how many hours does a person have until they can no longer
# edit or delete comments
COMMENT_EDIT_TIME_HOURS = 24


# user defined settings
if os.path.exists(absolute("settings_user.py")):
    from settings_user import * #@UnusedWildImport

# Preparser

if not DEBUG:
    PREPARSE_JS = "jsmin <%(in)s >%(out)s"
    PREPARSE_CSS = "sass --style compressed %(in)s %(out)s"
else:
    PREPARSE_JS = None
    PREPARSE_CSS = "sass %(in)s %(out)s"

# (folder to watch, folder to output to, output extension, command to run),
# output files's file extension will be replaced with output extension. (include the leading '.')
# command to run is optional. Use None if you just want to copy the output.
# if you want another command to run, use %(in)s and %(out)s for the input and output files. 
PREPARSE_CHAIN = (
    (absolute(os.path.join('templates', 'pre', 'js')), absolute(os.path.join('media', 'js')), '.pre.js', PREPARSE_JS),
    (absolute(os.path.join('templates', 'pre', 'css')), absolute(os.path.join('media', 'css')), '.pre.css', PREPARSE_CSS),
)

PREPARSE_CONTEXT_MODULE = 'preparse_context'

