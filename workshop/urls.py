from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'workbench/home.html'}, name="workbench.home"),
    url(r'^ajax/home/$', 'opensourcemusic.workshop.views.ajax_home', name="workbench.ajax_home"),
)
