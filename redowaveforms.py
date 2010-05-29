# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

import waveform
import os

from main.models import Song
import competitions
import competitions.design
import competitions.views

for song in Song.objects.all():
    print("redoing %s - %s..." % (song.band.title, song.title))
    mp3_safe_path = os.path.join(settings.MEDIA_ROOT, song.mp3_file)
    if song.waveform_img is not None:
        png_safe_path_relative = song.waveform_img
        png_safe_path = os.path.join(settings.MEDIA_ROOT, song.waveform_img)
    else:
        # create a waveform file path
        png_file_title = "%s - %s (%s).png" % (artist_name, title, compo.title)
        png_safe_path, png_safe_title = competitions.views.safe_file(os.path.join(settings.MEDIA_ROOT, 'compo', 'mp3'), png_file_title)
        png_safe_path_relative = os.path.join('compo','mp3',png_safe_title)


    try:
        waveform.draw(mp3_safe_path, png_safe_path,
            competitions.design.waveform_size,
            fgGradientCenter=competitions.design.waveform_center_color,
            fgGradientOuter=competitions.design.waveform_outer_color)
    except IOError:
        print("IOError")

    song.waveform_img = png_safe_path_relative
    song.save()
