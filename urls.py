from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template, redirect_to
from django.contrib import admin
import django_cron
import os

admin.autodiscover()
django_cron.autodiscover()

from opensourcemusic import settings

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
    (r'^register/$', 'opensourcemusic.main.views.user_register'),
    (r'^register/pending/$', direct_to_template, {'template': 'pending.html'}),
    (r'^confirm/(.+)/(.+)/$', 'opensourcemusic.main.views.confirm'),

    (r'^about/$', direct_to_template, {'template': 'about.html'}),
    (r'^policy/$', direct_to_template, {'template': 'policy.html'}),
    (r'^account/$', direct_to_template, {'template': 'account.html'}),
)
# exceptions to media url
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(settings.MEDIA_ROOT, 'static')}),
    )

