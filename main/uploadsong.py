from django.db.models import Q
from django.conf import settings
from main.upload import *
from main.common import create_hash
from main.models import Song
from workshop.models import *

import os
import stat
import shutil
import tempfile

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import error as MutagenID3Error

import waveform
import daw

from main import design

def studio_extensions():
    return [item for sublist in [x.fileExtensions for x in daw._class_dict.values()] for item in sublist]

def obfuscated_url(band):
    return os.path.join('band', band.url, create_hash(16))   

def generate_waveform(song, mp3_file):
    png_tmp_handle = tempfile.NamedTemporaryFile(mode='r+b', suffix='.png')
    waveform.draw(mp3_file, png_tmp_handle.name, design.waveform_size,
        fgGradientCenter=design.waveform_center_color,
        fgGradientOuter=design.waveform_outer_color)
    # move to storage
    song.waveform_img = os.path.join(obfuscated_url(song.band), clean_filename(song.displayString()))
    import storage
    storage.engine.store(png_tmp_handle.name, song.waveform_img, reducedRedundancy=True)
    # clean up
    png_tmp_handle.close()

def upload_song(user, file_mp3_handle=None, file_source_handle=None, max_song_len=None, band=None, song_title=None, song_album=None):
    """
    inputs: 
        user:               the person uploading stuff
        file_mp3_handle:    the handle from the form
        file_source_handle: the handle from the form. need to also pass user if you want this to work.
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
        song:       new song model. it will have been saved, but then more
                    things added to it so it needs to be saved again. it will
                    have the following fields properly populated:
            owner
            source_file
            waveform_img
            mp3_file
            band
            title
            length
            samples
            effects
            generators
    """
    data = {
        'success': False,
        'song': None,
    }

    assert band != None, "Band parameter isn't optional."
    assert song_title != None, "Song title parameter isn't optional."

    song = Song()
    song.band = band
    song.owner = user
    song.title = song_title
    song.length = 0
    song.album = song_album

    if file_mp3_handle != None:
        # upload mp3 file to temp folder
        mp3_tmp_handle = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        upload_file_h(file_mp3_handle, mp3_tmp_handle)
        mp3_tmp_handle.close()

        # read the length tag
        try:
            audio = MP3(mp3_tmp_handle.name, ID3=EasyID3)
            song.length = audio.info.length
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

        # pick a path for the mp3 file. obscure the URL so that people can't steal songs
        song.mp3_file = os.path.join(obfuscated_url(band), clean_filename(song.displayString() + '.mp3'))

        generate_waveform(song, mp3_tmp_handle.name)

        # move mp3 file to storage
        move_to_storage(mp3_tmp_handle.name, song.mp3_file)

    # upload the source file
    if file_source_handle != None:
        # save so we can use the ManyToManyFields 
        song.save()

        # upload project file to temp file
        handle = tempfile.NamedTemporaryFile(delete=False)
        upload_file_h(file_source_handle, handle)
        handle.close()

        parts = file_source_handle.name.split('.')
        if len(parts) > 0:
            source_ext = parts[-1]
        else:
            source_ext = None
        if song_album != None:
            source_file_title = "%s - %s (%s)" % (band.title, song_title, song_album)
        else:
            source_file_title = "%s - %s" % (band.title, song_title)

        # read the project file with the daw
        try:
            dawProject = daw.load(handle.name)
            dawExt = dawProject.extension() 

            # assign the correct studio
            try:
                song.studio = Studio.objects.get(identifier=dawProject.identifier)
            except Studio.DoesNotExist:
                pass
            

            stuff = (
                (dawProject.generators(), GeneratorDependency, song.generators),
                (dawProject.effects(), EffectDependency, song.effects),
            )
            for plugins, PluginModel, songField in stuff:
                for plugin in plugins:
                    # if it's an invalid name, ignore
                    if plugin.strip() == '':
                        continue

                    # see if it already exists
                    depObjects = PluginModel.objects.filter(title=plugin)
                    if depObjects.count() == 0:
                        # create it
                        depObject = PluginModel()
                        depObject.title = plugin
                        depObject.save()
                    else:
                        depObject = depObjects[0]

                    # add it as a dependency
                    songField.add(depObject)

            samples = dawProject.samples()
            for sample in samples:
                # if it's an invalid name, ignore
                if sample.strip() == '':
                    continue

                path, title = os.path.split(sample)

                # create the dependency
                dep = SampleDependency()
                dep.title = title
                dep.song = song
                    
                # if the title matches anthing the user or band has already uploaded,
                # establish a link.
                existing_samples = UploadedSample.objects.filter(title=title).filter(Q(user=user)|Q(band=band))

                if existing_samples.count() > 0:
                    # TODO: handle title ambiguity
                    # copy the dependency to this song
                    existing_sample = existing_samples[0]
                    dep.uploaded_sample = existing_sample

                dep.save()

            if dawExt:
                source_file_title += "." + dawExt

            usingDaw = True
        except daw.exceptions.LoadError:
            usingDaw = False
            # ok forget about processing it with the daw
            # add the extension from before
            if source_ext:
                source_file_title += "." + source_ext

        song.source_file = os.path.join(obfuscated_url(band), clean_filename(source_file_title))

        if usingDaw:
            out_handle = tempfile.NamedTemporaryFile(mode='r+b')
            dawProject.save(out_handle.name)
            import storage
            storage.engine.store(out_handle.name, song.source_file)
            out_handle.close()
            os.remove(handle.name)
        else:
            move_to_storage(handle.name, song.source_file)

    data['song'] = song
    data['success'] = True
    return data

