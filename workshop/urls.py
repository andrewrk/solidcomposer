from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'workbench/home.html'}, name="workbench.home"),

    url(r'^ajax/home/$', 'workshop.views.ajax_home', name="workbench.ajax_home"),
    url(r'^ajax/invite/ignore/$', 'workshop.views.ajax_ignore_invite', name="workbench.ajax_ignore_invite"),
    url(r'^ajax/invite/accept/$', 'workshop.views.ajax_accept_invite', name="workbench.ajax_accept_invite"),

    url(r'^create/$', 'workshop.views.create_band', name="workbench.create_band"),

    url(r'^band/(\d+)/$', 'workshop.views.band', name="workbench.band"),
    url(r'^band/(\d+)/create/$', 'workshop.views.create_project', name="workbench.create_project"),
    url(r'^band/(\d+)/project/(\d+)/$', 'workshop.views.project', name="workbench.project"),
)
