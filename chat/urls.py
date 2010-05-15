from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^ajax/hear/$', 'opensourcemusic.chat.views.ajax_hear', name="chat.hear"),
    url(r'^ajax/say/$', 'opensourcemusic.chat.views.ajax_say', name="chat.say"),
    url(r'^ajax/online/$', 'opensourcemusic.chat.views.ajax_onliners', name="chat.onliners"),
)
