from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'music/home.html'}, name="music.home"),
    url(r'^band/(.+)/$', 'music.views.band', name="music.band"),
)

