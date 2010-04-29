from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin
import django_cron

admin.autodiscover()
django_cron.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'home.html'}),
    (r'^arena/', include('opensourcemusic.competitions.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^ajax/login_state/$', 'opensourcemusic.main.views.ajax_login_state'),
    (r'^ajax/login/$', 'opensourcemusic.main.views.ajax_login'),
    (r'^ajax/logout/$', 'opensourcemusic.main.views.ajax_logout'),
    (r'^ajax/chat/$', 'opensourcemusic.main.views.ajax_chat'),
    (r'^ajax/chat/say/$', 'opensourcemusic.main.views.ajax_say'),
    (r'^ajax/chat/online/$', 'opensourcemusic.main.views.ajax_onliners'),

    (r'^login/$', 'opensourcemusic.main.views.user_login'),
    (r'^logout/$', 'opensourcemusic.main.views.user_logout'),
)

