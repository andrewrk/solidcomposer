from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'workbench/home.html'}, name="workbench.home"),

    url(r'^ajax/home/$', 'workshop.views.ajax_home', name="workbench.ajax_home"),
    url(r'^ajax/invite/ignore/$', 'workshop.views.ajax_ignore_invite', name="workbench.ajax_ignore_invite"),
    url(r'^ajax/invite/accept/$', 'workshop.views.ajax_accept_invite', name="workbench.ajax_accept_invite"),
    url(r'^ajax/create_band/$', 'workshop.views.ajax_create_band', name="workbench.ajax_create_band"),
    url(r'^ajax/project_filters/$', 'workshop.views.ajax_project_filters', name="workbench.ajax_project_filters"),
    url(r'^ajax/project_list/$', 'workshop.views.ajax_project_list', name="workbench.ajax_project_list"),
    url(r'^ajax/project/$', 'workshop.views.ajax_project', name="workbench.ajax_project"),
    url(r'^ajax/upload_samples/$', 'workshop.views.ajax_upload_samples', name="workbench.ajax_upload_samples"),

    url(r'^band/(\d+)/$', 'workshop.views.band', name="workbench.band"),
    url(r'^band/(\d+)/settings/$', 'workshop.views.band_settings', name="workbench.band_settings"),
    url(r'^band/(\d+)/create/$', 'workshop.views.create_project', name="workbench.create_project"),
    url(r'^band/(\d+)/project/(\d+)/$', 'workshop.views.project', name="workbench.project"),
)
