from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url('^$', direct_to_template, {'template': 'arena/home.html'},
        name="arena.home"),
    url('^ajax/available/$', 'opensourcemusic.competitions.views.ajax_available',
        name="arena.ajax_available"),
    url('^ajax/owned/$', 'opensourcemusic.competitions.views.ajax_owned', name="arena.ajax_owned"),
    url('^ajax/bookmark/(\d+)/$', 'opensourcemusic.competitions.views.ajax_bookmark',
        name="arena.ajax_bookmark"),
    url('^ajax/remove/(\d+)/$', 'opensourcemusic.competitions.views.ajax_unbookmark',
        name="arena.ajax_unbookmark"),
    url('^ajax/compo/(\d+)/$', 'opensourcemusic.competitions.views.ajax_compo',
        name="arena.ajax_compo"),
    url('^ajax/vote/(\d+)/$', 'opensourcemusic.competitions.views.ajax_vote',
        name="arena.ajax_vote"),
    url('^ajax/unvote/(\d+)/$', 'opensourcemusic.competitions.views.ajax_unvote',
        name="arena.ajax_unvote"),
    url('^ajax/submit-entry/$', 'opensourcemusic.competitions.views.ajax_submit_entry',
        name="arena.ajax_submit_entry"),

    url('^create/$', 'opensourcemusic.competitions.views.create',
        name="arena.create"),
    url('^compete/(\d+)/$', 'opensourcemusic.competitions.views.competition',
        name="arena.compete"),
)
