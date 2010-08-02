from django.conf.urls.defaults import * #@UnusedWildImport
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^ajax/hear/$', 'chat.views.ajax_hear', name="chat.hear"),
    url(r'^ajax/say/$', 'chat.views.ajax_say', name="chat.say"),
    url(r'^ajax/online/$', 'chat.views.ajax_onliners', name="chat.onliners"),
)
