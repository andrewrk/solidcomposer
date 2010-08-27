from django.db.models import Q
from main import design
from main.common import create_hash, zip_walk, file_hash
from main.models import Song, SongCommentNode, BandMember
from main.upload import clean_filename, move_to_storage, upload_file_h
from mutagen.easyid3 import EasyID3
from mutagen.id3 import error as MutagenID3Error
from mutagen.mp3 import MP3
from workshop.models import SampleFile, UploadedSample, SampleDependency, Studio, \
    PluginDepenency
import daw
import os
import tempfile
import waveform

IGNORED_PLUGINS = (
    'Sampler',
    'Fruity Wrapper',
)

def flatten_list(lst):
    return [item for sublist in lst for item in sublist]

def studio_extensions():
    return flatten_list([x.fileExtensions for x in daw._class_dict.values()])

def obfuscated_url(band):
    return os.path.join('band', band.url, create_hash(16))   

def generate_waveform(song, mp3_file, filename_appendix=""):
    suffix = '.png'
    png_tmp_handle = tempfile.NamedTemporaryFile(mode='r+b', suffix=suffix)
    waveform.draw(mp3_file, png_tmp_handle.name, design.waveform_size,
        fgGradientCenter=design.waveform_center_color,
        fgGradientOuter=design.waveform_outer_color)
    # move to storage
    song.waveform_img = os.path.join(obfuscated_url(song.band), clean_filename(song.displayString()) + filename_appendix + suffix)
    import storage
    storage.engine.store(png_tmp_handle.name, song.waveform_img, reducedRedundancy=True)
    # clean up
    png_tmp_handle.close()

def handle_sample_file(filename, file_id, user, band, callback=None):
    """
    creates the database entries necessary for filename as a sample.
    moves filename to storage or deletes it if there was a problem.
    increments the band's used space. be sure to save after calling.

    if callback is defined, it will be called with each UploadedSample created.
    """
    if band.is_read_only():
        os.remove(filename)
        return

    # check if it is a zip file
    skipExts = studio_extensions()
    _name, ext = os.path.splitext(filename)
    if ext.lower() == '.zip':
        def zipCallback(extracted_file):
            _path, title = os.path.split(extracted_file)

            # skip studio files when uploading sample zips
            _prefix, ext = os.path.splitext(title)
            if ext[1:].lower() in skipExts:
                os.remove(extracted_file)
                return

            handle_sample_file(extracted_file, title, user, band, callback)

        zip_walk(filename, zipCallback)
        os.remove(filename)
        return

    # check the hash
    md5sum = file_hash(filename)

    try:
        existing_sample = SampleFile.objects.get(hex_digest=md5sum)
    except SampleFile.DoesNotExist:
        existing_sample = None

    sample = UploadedSample()
    sample.title = file_id
    skip_byte_count = False
    if existing_sample is not None:
        sample.sample_file = existing_sample

        # if it already exists, don't create a duplicate
        existing_uploaded_samples = UploadedSample.objects.filter(user=user, band=band, sample_file=existing_sample)
        if existing_uploaded_samples.count() > 0:
            if callback is not None:
                existing_uploaded_sample = existing_uploaded_samples[0]
                callback(existing_uploaded_sample)
            os.remove(filename)
            return

        # if user or user's band already uploaded it, don't count it
        # against the band's quota.
        skip_byte_count = UploadedSample.objects.filter(title=sample.title).filter(Q(user=user)|Q(band=band)).count() > 0
    else:
        # pick a good path for the sample
        sample_path = os.path.join('sample', md5sum)

        # create the SampleFile
        sf = SampleFile()
        sf.hex_digest = md5sum
        sf.path = sample_path
        sf.save()

        # copy it to good path
        import storage
        storage.engine.store(filename, sample_path) 

        sample.sample_file = sf

    sample.user = user
    sample.band = band
    sample.save()

    if callback is not None:
        callback(sample)

    # if any songs of any of the user's bands are missing this sample,
    # resolve the dependency.
    user_bands = BandMember.objects.filter(user=user, role__in=[BandMember.BAND_MEMBER, BandMember.MANAGER]).values_list('band', flat=True)
    deps = SampleDependency.objects.filter(title=sample.title, song__band__in=user_bands)
    for dep in deps:
        dep.uploaded_sample = sample
        dep.save()

    if not skip_byte_count:
        # count it against the band's size quota
        band.used_space += os.path.getsize(filename)

    os.remove(filename)

def handle_project_file(filename, user, song, filename_appendix=""):
    """
    creates the database entries necessary for filename as the project for song.
    moves filename to storage or deletes it if there is a problem.
    increments the band's used space. be sure to save song and song.band after calling.
    """
    _prefix, ext = os.path.splitext(filename)
    profile = user.get_profile()

    # handle zip files
    if ext.lower() == '.zip':
        studioExts = studio_extensions()
        song.studio = None
        def zipCallback(extracted_filename):
            _path, title = os.path.split(extracted_filename)
            _prefix, ext = os.path.splitext(extracted_filename)
            if ext[1:].lower() in studioExts:
                if song.studio is None:
                    handle_project_file(extracted_filename, user, song, filename_appendix=filename_appendix)
            else:
                handle_sample_file(extracted_filename, title, user, song.band)

        zip_walk(filename, zipCallback)
        os.remove(filename)
        return

    # read the project file with the daw
    source_file_title = song.displayString()
    profile_save_required = False
    try:
        dawProject = daw.load(filename)
        dawExt = dawProject.extension() 

        # assign the correct studio
        try:
            song.studio = Studio.objects.get(identifier=dawProject.identifier)

            # assume the user owns the studio
            profile.studios.add(song.studio)
            profile_save_required = True
        except Studio.DoesNotExist:
            pass

        stuff = (
            (dawProject.generators(), PluginDepenency.GENERATOR),
            (dawProject.effects(), PluginDepenency.EFFECT),
        )
        for plugins, plugin_type in stuff:
            for plugin in plugins:
                # if it's an invalid name, ignore
                if plugin.strip() == '':
                    continue

                if plugin in IGNORED_PLUGINS:
                    continue

                # see if it already exists
                deps = PluginDepenency.objects.filter(title=plugin)
                if deps.count() == 0:
                    # create it
                    dep = PluginDepenency()
                    dep.title = plugin
                    dep.plugin_type = plugin_type
                    dep.save()
                else:
                    dep = deps[0]

                # add it as a dependency
                song.plugins.add(dep)

                # assume that the user owns this dependency
                if profile.assume_uploaded_plugins_owned:
                    profile.plugins.add(dep)
                    profile_save_required = True

        samples = dawProject.samples()
        for sample in samples:
            # if it's an invalid name, ignore
            if sample.strip() == '':
                continue

            _path, title = os.path.split(sample)

            # create the dependency
            dep = SampleDependency()
            dep.title = title
            dep.song = song
                
            # if the title matches anthing the user or band has already uploaded,
            # establish a link.
            existing_samples = UploadedSample.objects.filter(title=title).filter(Q(user=user)|Q(band=song.band))

            if existing_samples.count() > 0:
                # TODO: handle title ambiguity
                # copy the dependency to this song
                existing_sample = existing_samples[0]
                dep.uploaded_sample = existing_sample

            dep.save()

        if dawExt:
            source_file_title += filename_appendix + "." + dawExt

        usingDaw = True
    except daw.exceptions.LoadError:
        usingDaw = False
        # ok forget about processing it with the daw
        # add the extension from before
        source_file_title += filename_appendix + ext
    finally:
        if profile_save_required:
            profile.save()

    song.source_file = os.path.join(obfuscated_url(song.band), clean_filename(source_file_title))

    if usingDaw:
        out_handle = tempfile.NamedTemporaryFile(mode='r+b')
        dawProject.save(out_handle.name)

        # count it against the band's size quota
        song.band.used_space += os.path.getsize(out_handle.name)

        # move to storage
        import storage
        storage.engine.store(out_handle.name, song.source_file)
        out_handle.close()

        os.remove(filename)
    else:
        # count it against the band's size quota
        song.band.used_space += os.path.getsize(filename)
        # move to storage
        move_to_storage(filename, song.source_file)

    song.save()

def handle_mp3_upload(file_mp3_handle, song, max_song_len=None, filename_appendix=""):
    data = {'success': False}

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

    audio['artist'] = song.band.title
    if song.title != None:
        audio['title'] = song.title
    if song.album != None:
        audio['album'] = song.album

    try:
        audio.save()
    except:
        data['reason'] = design.unable_to_save_id3_tags
        return data

    # pick a path for the mp3 file. obscure the URL so that people can't steal songs
    song.mp3_file = os.path.join(obfuscated_url(song.band), clean_filename(song.displayString() + filename_appendix + '.mp3'))

    generate_waveform(song, mp3_tmp_handle.name, filename_appendix)

    # count mp3 against the band's size quota
    song.band.used_space += os.path.getsize(mp3_tmp_handle.name)

    # move mp3 file to storage
    move_to_storage(mp3_tmp_handle.name, song.mp3_file)

    song.band.save()
    data = {'success': True}
    return data

def handle_project_upload(file_source_handle, user, song, filename_appendix=""):
    # upload project file to temp file
    _source_prefix, source_ext = os.path.splitext(file_source_handle.name)
    handle = tempfile.NamedTemporaryFile(suffix=source_ext, delete=False)
    upload_file_h(file_source_handle, handle)
    handle.close()

    handle_project_file(handle.name, user, song, filename_appendix=filename_appendix)

def upload_song(user, file_mp3_handle=None, file_source_handle=None, max_song_len=None, band=None, song_title=None, song_album="", song_comments="", filename_appendix=""):
    """
    inputs: 
        user:               the person uploading stuff
        file_mp3_handle:    the handle from the form
        file_source_handle: the handle from the form. need to also pass user if you want this to work.
        max_song_len:       how many seconds long a song can be. None means unlimited.
        band:               band model - who to attribute the song to.
        song_title:         id3 title to enforce upon the mp3
        song_album:         id3 album to enforce upon the mp3
        song_comments:      the author's own comments for the song.
        filename_appendix:  use this if you want to add something to the filename, before the extension.

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
            album
            length
            studio
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

    # save so we can use relational fields
    song.save()
    
    # create the root node for song comments
    node = SongCommentNode()
    node.song = song
    node.owner = user
    node.content = song_comments
    node.save()

    song.comment_node = node

    if file_mp3_handle != None:
        result = handle_mp3_upload(file_mp3_handle, song, max_song_len, filename_appendix=filename_appendix)
        if not result['success']:
            song.delete()
            return result

    # upload the source file
    if file_source_handle != None:
        handle_project_upload(file_source_handle, user, song, filename_appendix=filename_appendix)

    # we incremented bytes_used in band, so save it now
    band.save()

    data['song'] = song
    data['success'] = True
    return data

