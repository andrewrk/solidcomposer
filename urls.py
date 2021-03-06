from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template, redirect_to

admin.autodiscover()

urlpatterns = patterns('',
    (r'^arena/', include('competitions.urls')),
    (r'^chat/', include('chat.urls')),
    (r'^workbench/', include('workshop.urls')),
    (r'^admin/', include(admin.site.urls)),

    url(r'^$', 'main.views.home', name='home'),

    url(r'^ajax/login_state/$', 'main.views.ajax_login_state', name="ajax_login_state"),
    # if you change this, change LOGIN_URL in settings too.
    url(r'^ajax/login/$', 'main.views.ajax_login', name="ajax_login"),
    url(r'^ajax/logout/$', 'main.views.ajax_logout', name="ajax_logout"),
    url(r'^ajax/comment/$', 'main.views.ajax_comment', name="ajax_comment"),
    url(r'^ajax/delete_comment/$', 'main.views.ajax_delete_comment', name="ajax_delete_comment"),
    url(r'^ajax/edit_comment/$', 'main.views.ajax_edit_comment', name="ajax_edit_comment"),

    url(r'^article/([\w\d-]+)/$', 'main.views.article', name='article'),

    url(r'^plans/$', 'main.views.plans', name='plans'),

    url(r'^user/(.+)/$', 'main.views.userpage', name='userpage'),
    url(r'^band/(.+)/$', 'main.views.bandpage', name='bandpage'),

    url(r'^login/$', 'main.views.user_login', name="user_login"),
    url(r'^logout/$', 'main.views.user_logout', name="user_logout"),
    url(r'^signup/$', 'main.views.user_register', name="register"),
    url(r'^signup/pending/$', 'main.views.register_pending', name="register_pending"),
    url(r'^signup/(.+)/$', 'main.views.user_register_plan', name="register_plan"),
    url(r'^confirm/(.+)/(.+)/$', 'main.views.confirm', name="confirm"),

    url(r'^contact/$', 'main.views.contact', name="contact"),
    
    url(r'^legal/$', direct_to_template, {'template': 'legal/home.html'}, name="legal"),
    url(r'^legal/privacy/$', direct_to_template, {'template': 'legal/policy.html'}, name="policy"),
    url(r'^legal/terms/$', direct_to_template, {'template': 'legal/terms.html'}, name="terms"),

    url(r'^account/$', 'main.views.account_plan', name="account"),
    url(r'^account/plan/$', 'main.views.account_plan', name="account.plan"),
    url(r'^account/email/$', 'main.views.account_email', name="account.email"),
    url(r'^account/preferences/$', 'main.views.account_preferences', name="account.preferences"),
    url(r'^account/password/$', 'main.views.account_password', name="account.password"),
    url(r'^account/password/reset/$', 'main.views.account_password_reset', name="account.password.reset"),

    url(r'^landing/$', 'main.views.landing', name='landing'),
    url(r'^dashboard/$', 'main.views.dashboard', name='dashboard'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^500/$', direct_to_template, {'template': '500.html'}, name='404'),
        url(r'^404/$', direct_to_template, {'template': '404.html'}, name='500'),
    )

