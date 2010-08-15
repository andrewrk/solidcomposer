from django.conf.urls.defaults import * #@UnusedWildImport
from django.contrib import admin
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',
    (r'^arena/', include('competitions.urls')),
    (r'^chat/', include('chat.urls')),
    (r'^workbench/', include('workshop.urls')),
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

    url(r'^contact/$', 'main.views.contact', name="contact"),
    url(r'^contact/thanks/$', direct_to_template, {'template': 'contact_thanks.html'}, name="contact_thanks"),
    
    url(r'^about/$', direct_to_template, {'template': 'about.html'}, name="about"),
    url(r'^privacy/$', direct_to_template, {'template': 'policy.html'}, name="policy"),
    url(r'^terms/$', direct_to_template, {'template': 'terms.html'}, name="terms"),
    url(r'^account/$', direct_to_template, {'template': 'account.html'}, name="account"),


    url(r'^500/$', direct_to_template, {'template': '500.html'}, name='500'),
    url(r'^404/$', direct_to_template, {'template': '404.html'}, name='404'),
)
