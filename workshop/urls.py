from django.conf.urls.defaults import * #@UnusedWildImport
from django.contrib import admin
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'workbench/home.html'}, name="workbench.home"),

    url(r'^ajax/home/$', 'workshop.views.ajax_home', name="workbench.ajax_home"),
    url(r'^ajax/invite/ignore/$', 'workshop.views.ajax_ignore_invite', name="workbench.ajax_ignore_invite"),
    url(r'^ajax/invite/accept/$', 'workshop.views.ajax_accept_invite', name="workbench.ajax_accept_invite"),
    url(r'^ajax/invite/create/$', 'workshop.views.ajax_create_invite', name="workbench.ajax_create_invite"),
    url(r'^ajax/invite/email/$', 'workshop.views.ajax_email_invite', name="workbench.ajax_email_invite"),
    url(r'^ajax/invite/username/$', 'workshop.views.ajax_username_invite', name="workbench.ajax_username_invite"),
    url(r'^ajax/create_band/$', 'workshop.views.ajax_create_band', name="workbench.ajax_create_band"),
    url(r'^ajax/project_filters/$', 'workshop.views.ajax_project_filters', name="workbench.ajax_project_filters"),
    url(r'^ajax/project_list/$', 'workshop.views.ajax_project_list', name="workbench.ajax_project_list"),
    url(r'^ajax/project/$', 'workshop.views.ajax_project', name="workbench.ajax_project"),
    url(r'^ajax/upload_samples/$', 'workshop.views.ajax_upload_samples', name="workbench.ajax_upload_samples"),
    url(r'^ajax/upload_samples_as_version/$', 'workshop.views.ajax_upload_samples_as_version', name="workbench.ajax_upload_samples_as_version"),
    url(r'^ajax/rename_project/$', 'workshop.views.ajax_rename_project', name="workbench.ajax_rename_project"),
    url(r'^ajax/dependency_ownership/$', 'workshop.views.ajax_dependency_ownership', name="workbench.ajax_dependency_ownership"),
    url(r'^ajax/provide_project/$', 'workshop.views.ajax_provide_project', name="workbench.ajax_provide_project"),
    url(r'^ajax/provide_mp3/$', 'workshop.views.ajax_provide_mp3', name="workbench.ajax_provide_mp3"),
    url(r'^ajax/checkout/$', 'workshop.views.ajax_checkout', name="workbench.ajax_checkout"),
    url(r'^ajax/checkin/$', 'workshop.views.ajax_checkin', name="workbench.ajax_checkin"),

    url(r'^create/$', 'workshop.views.create_band', name="workbench.create_band"),

    url(r'^band/(\d+)/$', 'workshop.views.band', name="workbench.band"),
    url(r'^band/(\d+)/settings/$', 'workshop.views.band_settings', name="workbench.band_settings"),
    url(r'^band/(\d+)/create/$', 'workshop.views.create_project', name="workbench.create_project"),
    url(r'^band/(\d+)/project/(\d+)/$', 'workshop.views.project', name="workbench.project"),
    url(r'^band/(\d+)/invite/$', 'workshop.views.band_invite', name="workbench.band_invite"),

    url(r'^download/zip/$', 'workshop.views.download_zip', name="workbench.download_zip"),
    url(r'^download/sample/(\d+)/(.+)/$', 'workshop.views.download_sample', name="workbench.download_sample"),
    url(r'^download/samples/$', 'workshop.views.download_sample_zip', name="workbench.download_sample_zip"),

    url(r'^plugin/(.+)/$', 'workshop.views.plugin', name="workbench.plugin"),
    url(r'^studio/(.+)/$', 'workshop.views.studio', name="workbench.studio"),

    url(r'^redeem/(.+)/$', 'workshop.views.redeem_invitation', name="workbench.redeem_invitation"),
)
