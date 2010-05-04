# Django settings for opensourcemusic project.
# you can override any of this with settings_user.py, which does not get
# committed to source control.

import os
import datetime

def absolute(relative_path):
    """
    make a relative path absolute
    """
    return os.path.join(os.path.dirname(__file__), relative_path)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Andy Kelley', 'superjoe30@gmail.com'),
)

MANAGERS = ADMINS

# this is something you may want to override in settings_user.py
# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_ENGINE = 'mysql'           
# Or path to database file if using sqlite3.
DATABASE_NAME = 'opensourcemusic'
# Not used with sqlite3.
DATABASE_USER = 'opensourcemusic'             
# Not used with sqlite3.
DATABASE_PASSWORD = 'dev'         
# Set to empty string for localhost. Not used with sqlite3.
DATABASE_HOST = ''             
# Set to empty string for default. Not used with sqlite3.
DATABASE_PORT = ''             


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.

# set this to None as soon as django supports it.
# this is something you may want to override in settings_user.py
TIME_ZONE = 'America/Phoenix'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = absolute('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
# this is something you may want to override in settings_user.py
MEDIA_URL = 'http://localhost:8080/django/opensourcemusic/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# this is something you may want to override in settings_user.py
ADMIN_MEDIA_PREFIX = 'http://localhost:8080/django/opensourcemusic/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '2_l-92-j(^)a=vsynmsw1d(efi!w@w#j#v@ucv^2i7cfsk=!8='

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'opensourcemusic.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    absolute('templates'),
)

# where processed java script files will be output to. folder structure
# will be mirrored.
PREPARSE_OUTPUT = os.path.join(MEDIA_ROOT, 'js', 'pre')

# these will be processed with django's templating system and moved
# to the PREPARSE_OUTPUT folder, mirroring folder structure.
PREPARSE_DIR = os.path.join('templates', 'preparsed')

# the dictionary that will be available to your preparsed code.
PREPARSE_CONTEXT = {
    'server_time': datetime.datetime.today().strftime("%B %d, %Y %H:%M:%S"),
}

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.core.context_processors.auth',
	'django.core.context_processors.debug',
	'django.core.context_processors.i18n',
	'django.core.context_processors.media',
    'django.core.context_processors.request',
    'opensourcemusic.context.global_values',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'south',
    'django_cron',
    'opensourcemusic.main',
    'opensourcemusic.competitions',
)

LOGIN_URL = "/login/"
AUTH_PROFILE_MODULE = 'main.Profile'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

# how many seconds to wait before generating leave messages for chatters
CHAT_TIMEOUT = 60

# maximum length of competition tracks in seconds
COMPO_ENTRY_MAX_LEN = 10 * 60

# how many seconds to wait between tracks in listening party for buffering
LISTENING_PARTY_BUFFER_TIME = 10

# how many bytes to limit uploads to
FILE_UPLOAD_SIZE_CAP = 1024 * 1024 * 10  # 20 MB

if os.path.exists("settings_user.py"):
    from settings_user import *

