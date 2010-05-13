from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^ajax/hear/$', 'opensourcemusic.chat.views.ajax_hear'),
    (r'^ajax/say/$', 'opensourcemusic.chat.views.ajax_say'),
    (r'^ajax/online/$', 'opensourcemusic.chat.views.ajax_onliners'),
)
