#!/usr/bin/python

import os, sys
sys.path.append('/home/andy/dev/theburningawesome')
sys.path.append('/home/andy/dev')

def solid():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'solidcomposer.settings'

def tba():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'theburningawesome.settings'

tba()

from main.models import Band
from theburningawesome.projectmanager import models as tba_models

project = tba_models.Project.objects.order_by('-pk')[0]
print project.title


solid()

band = Band.objects.order_by('-pk')[0]
print band.title

