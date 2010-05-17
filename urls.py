from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template, redirect_to
from django.contrib import admin
import django_cron
import os

admin.autodiscover()
django_cron.autodiscover()

from opensourcemusic import settings

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'home.html'}, name='home'),
    (r'^arena/', include('opensourcemusic.competitions.urls')),
    (r'^chat/', include('opensourcemusic.chat.urls')),
    (r'^workbench/', include('opensourcemusic.workshop.urls')),
    (r'^music/', include('opensourcemusic.music.urls')),
    (r'^admin/', include(admin.site.urls)),

    url(r'^user/(.+)/$', 'opensourcemusic.main.views.userpage', name='userpage'),

    url(r'^ajax/login_state/$', 'opensourcemusic.main.views.ajax_login_state', name="ajax_login_state"),
    url(r'^ajax/login/$', 'opensourcemusic.main.views.ajax_login', name="ajax_login"),
    url(r'^ajax/logout/$', 'opensourcemusic.main.views.ajax_logout', name="ajax_logout"),

    url(r'^login/$', 'opensourcemusic.main.views.user_login', name="user_login"),
    url(r'^logout/$', 'opensourcemusic.main.views.user_logout', name="user_logout"),
    url(r'^register/$', 'opensourcemusic.main.views.user_register', name="register"),
    url(r'^register/pending/$', direct_to_template, {'template': 'pending.html'}, name="register_pending"),
    url(r'^confirm/(.+)/(.+)/$', 'opensourcemusic.main.views.confirm', name="confirm"),

    url(r'^about/$', direct_to_template, {'template': 'about.html'}, name="about"),
    url(r'^policy/$', direct_to_template, {'template': 'policy.html'}, name="policy"),
    url(r'^account/$', direct_to_template, {'template': 'account.html'}, name="account"),
)
# exceptions to media url
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(settings.MEDIA_ROOT, 'static')}),
    )

