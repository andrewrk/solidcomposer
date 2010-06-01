from competitions.models import *
from django.contrib import admin

stuff = (
)

map(lambda x: admin.site.register(x), stuff)

