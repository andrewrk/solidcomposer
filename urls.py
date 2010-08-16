from django.conf.urls.defaults import *
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
    url(r'^ajax/login/$', 'main.views.ajax_login', name="ajax_login"),
    url(r'^ajax/logout/$', 'main.views.ajax_logout', name="ajax_logout"),
    url(r'^ajax/comment/$', 'main.views.ajax_comment', name="ajax_comment"),
    url(r'^ajax/delete_comment/$', 'main.views.ajax_delete_comment', name="ajax_delete_comment"),
    url(r'^ajax/edit_comment/$', 'main.views.ajax_edit_comment', name="ajax_edit_comment"),

    url(r'^plans/$', 'main.views.plans', name='plans'),

    url(r'^user/(.+)/$', 'main.views.userpage', name='userpage'),
    url(r'^band/(.+)/$', 'main.views.bandpage', name='bandpage'),

    url(r'^login/$', 'main.views.user_login', name="user_login"),
    url(r'^logout/$', 'main.views.user_logout', name="user_logout"),
    url(r'^register/$', 'main.views.user_register', name="register"),
    url(r'^register/pending/$', direct_to_template, {'template': 'pending.html'}, name="register_pending"),
    url(r'^confirm/(.+)/(.+)/$', 'main.views.confirm', name="confirm"),

    url(r'^contact/$', 'main.views.contact', name="contact"),
    url(r'^contact/thanks/$', direct_to_template, {'template': 'contact_thanks.html'}, name="contact_thanks"),
    
    url(r'^privacy/$', direct_to_template, {'template': 'policy.html'}, name="policy"),
    url(r'^terms/$', direct_to_template, {'template': 'terms.html'}, name="terms"),
    url(r'^account/$', 'main.views.account_plan', name="account"),
    url(r'^account/plan/$', 'main.views.account_plan', name="account.plan"),
    url(r'^account/email/$', 'main.views.account_email', name="account.email"),
    url(r'^account/password/$', 'main.views.account_password', name="account.password"),
    url(r'^account/password/reset/$', 'main.views.account_password_reset', name="account.password.reset"),
    url(r'^account/password/reset/ok/$', direct_to_template, {'template': 'account/password_reset_ok.html'}, name="account.password.reset.ok"),
    url(r'^account/password/ok/$', direct_to_template, {'template': 'account/password_ok.html'}, name="account.password.ok"),

    url(r'^landing/$', 'main.views.landing', name='landing'),
    url(r'^info/$', direct_to_template, {'template': 'info.html'}, name='info'),
    url(r'^dashboard/$', 'main.views.dashboard', name='dashboard'),

    # for testing purposes
    url(r'^500/$', direct_to_template, {'template': '500.html'}, name='500'),
    url(r'^404/$', direct_to_template, {'template': '404.html'}, name='404'),
)
