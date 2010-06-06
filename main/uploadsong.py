import settings
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
    song.owner = user

    # save so we can use the ManyToManyFields 
    song.save()

    # upload the source file
    if file_source_handle != None:
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
            

            generators = dawProject.generators()
            for generator in generators:
                # see if it already exists
                genObjects = GeneratorDependency.objects.filter(title=generator)
                if genObjects.count() == 0:
                    # create it
                    genObject = GeneratorDependency()
                    genObject.title = generator
                    genObject.save()
                else:
                    genObject = genObjects[0]

                # add it as a dependency 
                song.generators.add(genObject)

            effects = dawProject.effects()
            for effect in effects:
                # see if it already exists
                effObjects = EffectDependency.objects.filter(title=effect)
                if effObjects.count() == 0:
                    # create it
                    effObject = EffectDependency()
                    effObject.title = effect
                    effObject.save()
                else:
                    effObject = effObjects[0]

                # add it as a dependency 
                song.effects.add(effObject)

            samples = dawProject.samples()
            for sample in samples:
                title = sample.split('/')[-1]
                # if the title matches anthing the user has already uploaded,
                # establish a link.
                user_samples = UserSampleDependency.objects.filter(user=user, title=title)

                if user_samples.count() > 0:
                    # user has already uploaded this file. 
                    user_sample = user_samples[0]
                    dep = SampleDependency()
                    dep.title = user_sample.title
                    dep.sample_file = user_sample.sample_file
                    dep.save()
                    song.samples.add(dep)
                    continue

                # next check the band's dependencies
                band_samples = BandSampleDependency.objects.filter(band=band, title=title)

                if band_samples.count() > 0:
                    # band has already uploaded this file.
                    band_sample = band_samples[0]
                    dep = SampleDependency()
                    dep.title = band_sample.title
                    dep.sample_file = band_sample.sample_file
                    dep.save()
                    song.samples.add(dep)
                    continue

                # unresolved dependency
                dep = BandSampleDependency()
                dep.band = band
                dep.title = title
                dep.save()
                song.samples.add(dep)
            
            if dawExt:
                source_file_title += "." + dawExt

            usingDaw = True
        except daw.exceptions.LoadError:
            usingDaw = False
            # ok forget about processing it with the daw
            # add the extension from before
            if source_ext:
                source_file_title += "." + source_ext

        source_safe_path, source_safe_file_title = safe_file(os.path.join(settings.MEDIA_ROOT, media_path), source_file_title)
        source_safe_path_relative = os.path.join(media_path, source_safe_file_title)

        song.source_file = source_safe_path_relative

        if usingDaw:
            dawProject.save(source_safe_path)
            os.remove(handle.name)
        else:
            shutil.move(handle.name, source_safe_path)

        # give it read permissions
        os.chmod(source_safe_path, stat.S_IWUSR|stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)


    data['song'] = song
    data['success'] = True
    return data

