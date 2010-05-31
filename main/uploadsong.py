import settings
from main.upload import *
from main.common import create_hash
from main.models import Song

import os
import stat
import shutil
import tempfile

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import error as MutagenID3Error

import waveform

from main import design

def upload_song(file_mp3_handle=None, file_source_handle=None, max_song_len=None, band=None, song_title=None, song_album=None):
    """
    inputs: 
        file_mp3_handle:    the handle from the form
        file_source_handle: ditto
        max_song_len:       how many seconds long a song can be. None means unlimited.
        band:               band model - who to attribute the song to.
        song_title:         id3 title to enforce upon the mp3
        song_album:         id3 album to enforce upon the mp3

    * uploads the mp3 and source file if applicable
    * creates the proper files and id3 tags
    * generates the waveform image

    outputs a dict:
        success:    boolean - whether it was successful or not
        reason:     string - what went wrong if success is False.
        song:       new unsaved song model with following fields properly populated:
            source_file
            waveform_img
            mp3_file
            band
            title
            length
            
    """
    data = {
        'success': False,
        'song': None,
    }

    assert band != None, "Band parameter isn't optional."

    if file_mp3_handle != None:
        # upload mp3 file to temp folder
        handle = tempfile.NamedTemporaryFile(suffix='mp3', delete=False)
        upload_file_h(file_mp3_handle, handle)
        handle.close()

        # read the length tag
        try:
            audio = MP3(handle.name, ID3=EasyID3)
            audio_length = audio.info.length
        except:
            data['reason'] = design.invalid_mp3_file
            return data

        # reject if invalid
        if audio.info.sketchy:
            data['reason'] = design.sketchy_mp3_file
            return data

        # reject if too long
        if max_song_len != None:
            if audio.info.length > max_song_len:
                data['reason'] = design.song_too_long
                return data

        # enforce ID3 tags
        try:
            audio.add_tags(ID3=EasyID3)
        except MutagenID3Error:
            pass

        audio['artist'] = band.title
        if song_title != None:
            audio['title'] = song_title
        if song_album != None:
            audio['album'] = song_album

        try:
            audio.save()
        except:
            data['reason'] = design.unable_to_save_id3_tags
            return data

        # pick a nice safe unique path for mp3_file, source_file, and wave form
        # obscure the URL so that people can't steal songs
        hash_str = create_hash(16)
        media_path = os.path.join('band', band.folder, hash_str)
        os.makedirs(os.path.join(settings.MEDIA_ROOT, media_path))

        if song_album != None:
            mp3_file_title = "%s - %s (%s).mp3" % (band.title, song_title, song_album)
            png_file_title = "%s - %s (%s).png" % (band.title, song_title, song_album)
        else:
            mp3_file_title = "%s - %s.mp3" % (band.title, song_title)
            png_file_title = "%s - %s.png" % (band.title, song_title)

        mp3_safe_path, mp3_safe_title = safe_file(os.path.join(settings.MEDIA_ROOT, media_path), mp3_file_title)
        mp3_safe_path_relative = os.path.join(media_path, mp3_safe_title)

        png_safe_path, png_safe_title = safe_file(os.path.join(settings.MEDIA_ROOT, media_path), png_file_title)
        png_safe_path_relative = os.path.join(media_path, png_safe_title)

        # move the mp3 file
        shutil.move(handle.name, mp3_safe_path)
        # give it read permissions
        os.chmod(mp3_safe_path, stat.S_IWUSR|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)

    song = Song()

    # upload the source file
    if file_source_handle != None:
        # extension of the source file
        parts = file_source_handle.name.split('.')
        if len(parts) > 0:
            source_ext = parts[-1]
            if song_album != None:
                source_file_title = "%s - %s (%s).%s" % (band.title, song_title, song_album, source_ext)
            else:
                source_file_title = "%s - %s.%s" % (band.title, song_title, source_ext)
        else:
            if song_album != None:
                source_file_title = "%s - %s (%s)" % (band.title, song_title, song_album)
            else:
                source_file_title = "%s - %s" % (band.title, song_title)
        source_safe_path, source_safe_file_title = safe_file(os.path.join(settings.MEDIA_ROOT, media_path), source_file_title)
        source_safe_path_relative = os.path.join(media_path, source_safe_file_title)

        upload_file(file_source_handle, source_safe_path)
        song.source_file = source_safe_path_relative

    # generate the waveform image
    try:
        waveform.draw(mp3_safe_path, png_safe_path, design.waveform_size,
            fgGradientCenter=design.waveform_center_color,
            fgGradientOuter=design.waveform_outer_color)
        song.waveform_img = png_safe_path_relative
    except:
        pass

    song.mp3_file = mp3_safe_path_relative
    song.band = band
    song.title = song_title
    song.length = audio_length

    data['song'] = song
    data['success'] = True
    return data


