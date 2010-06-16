# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.conf import settings

import waveform
import os

from main.models import Song
from main.uploadsong import generate_waveform
import competitions
import competitions.design

import storage
import tempfile

for song in Song.objects.all():
    print("redoing %s - %s..." % (song.band.title, song.title))
    storage.engine.delete(song.waveform_img)
    # get the mp3 from storage
    mp3_handle = tempfile.NamedTemporaryFile(mode='r+b')
    storage.engine.retrieve(song.mp3_file, mp3_handle.name)
    main.uploadsong.generate_waveform(song, mp3_handle.name)
    # clean up
    mp3_handle.close()
    
    song.save()
