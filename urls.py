from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template, redirect_to
from django.contrib import admin
import os

admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    (r'^arena/', include('competitions.urls')),
    (r'^chat/', include('chat.urls')),
    (r'^workbench/', include('workshop.urls')),
    (r'^music/', include('music.urls')),
    (r'^admin/', include(admin.site.urls)),

    url(r'^$', direct_to_template, {'template': 'home.html'}, name='home'),

    url(r'^ajax/login_state/$', 'main.views.ajax_login_state', name="ajax_login_state"),
    url(r'^ajax/login/$', 'main.views.ajax_login', name="ajax_login"),
    url(r'^ajax/logout/$', 'main.views.ajax_logout', name="ajax_logout"),
    url(r'^ajax/comment/$', 'main.views.ajax_comment', name="ajax_comment"),
    url(r'^ajax/delete_comment/$', 'main.views.ajax_delete_comment', name="ajax_delete_comment"),
    url(r'^ajax/edit_comment/$', 'main.views.ajax_edit_comment', name="ajax_edit_comment"),

    url(r'^user/(.+)/$', 'main.views.userpage', name='userpage'),

    url(r'^login/$', 'main.views.user_login', name="user_login"),
    url(r'^logout/$', 'main.views.user_logout', name="user_logout"),
    url(r'^register/$', 'main.views.user_register', name="register"),
    url(r'^register/pending/$', direct_to_template, {'template': 'pending.html'}, name="register_pending"),
    url(r'^confirm/(.+)/(.+)/$', 'main.views.confirm', name="confirm"),

    url(r'^about/$', direct_to_template, {'template': 'about.html'}, name="about"),
    url(r'^policy/$', direct_to_template, {'template': 'policy.html'}, name="policy"),
    url(r'^account/$', direct_to_template, {'template': 'account.html'}, name="account"),
)
