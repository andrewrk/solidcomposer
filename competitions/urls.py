from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
	url('^$', direct_to_template, {'template': 'arena/home.html'}),
    url('^ajax/available/$', 'opensourcemusic.competitions.views.ajax_available'),
    url('^ajax/owned/$', 'opensourcemusic.competitions.views.ajax_owned'),

    url('^create/$', 'opensourcemusic.competitions.views.create'),
)
