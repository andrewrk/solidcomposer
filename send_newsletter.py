#!/usr/bin/python

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from main.common import send_html_mail
from django.template import RequestContext, Context, TemplateDoesNotExist
from django.template.loader import get_template
import sys
from main.models import Profile
from django.contrib.sites.models import Site

if len(sys.argv) < 3:
    print("Usage:\n{0} template_name subject\n\ntemplate_name should be the prefix of two templates ending in .html and .txt".format(sys.argv[0]))
    sys.exit(1)

# send mail to everybody who doesn't have newsletters turned off

template_name = sys.argv[1]
subject = sys.argv[2]

html = template_name + ".html"
txt = template_name + ".txt"
current_site = Site.objects.get_current()

for profile in Profile.objects.all():
    if profile.email_newsletter:
        print("Emailing {0}...".format(profile.user.username))
        context = Context({
            'user': profile.user,
            'host': current_site.domain,
        })
        message_txt = get_template(template_name + '.txt').render(context)
        message_html = get_template(template_name + '.html').render(context)
        send_html_mail(subject, message_txt, message_html, [profile.user.email])
    else:
        print("Skipping {0}...".format(profile.user.username))
