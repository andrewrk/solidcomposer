#!/usr/bin/python

# =============
# set the mapping between TBA users and SolidComposer users
# profile.pk -> user.pk
andy_old_id, andy_new_id = (1, 1)
tyler_old_id, tyler_new_id = (2, 20)
casey_old_id, casey_new_id = (4, 45)
# overwrite with localhost test environment (delete for production)
andy_old_id, andy_new_id = (1, 32)
tyler_old_id, tyler_new_id = (2, 34)
casey_old_id, casey_new_id = (4, 33)
# right from theburningawesome/settings.py
tba_media_root = '/home/andy/dev/theburningawesome/media/'

# =============
# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

from workshop.models import *
from main.models import *
from django.contrib.auth.models import User

from main.uploadsong import upload_song, handle_sample_file, handle_mp3_upload, \
    handle_project_upload

import simplejson as json
import os
from main import design

from django.core.files import File

def open_file(relative_path):
    if relative_path is None or relative_path == '':
        return None
    return File(open(os.path.join(tba_media_root, 'flp', relative_path), 'rb'))

tba_prof_to_sc_user_id = {
    andy_old_id: andy_new_id,
    tyler_old_id: tyler_new_id,
    casey_old_id: casey_new_id,
}
tba_prof_to_sc_user = dict([(k, User.objects.get(pk=v)) for k,v in tba_prof_to_sc_user_id.iteritems()])
andy = tba_prof_to_sc_user[andy_old_id]
tyler = tba_prof_to_sc_user[tyler_old_id]
casey = tba_prof_to_sc_user[casey_old_id]

# =====================
print("Importing from tba.json...")

data = json.loads(open('tba.json', 'r').read())

projects = {}
first_versions = {} # the versions that are #1
versions = {} # every version that is not #1
profiles = {}
comments = {}

for entry in data:
    model = entry['model']
    if model == 'projectmanager.project':
        projects[entry['pk']] = entry
    elif model == 'projectmanager.projectversion':
        if entry['fields']['version'] == 1:
            first_versions[entry['pk']] = entry
        else:
            versions[entry['pk']] = entry
    elif model == 'projectmanager.projectversioncomment':
        comments[entry['pk']] = entry
    elif model == 'main.profile':
        profiles[entry['pk']] = entry

skip_projects = [59]
# =====================

# if it already exists, delete the band
try:
    tba_band = Band.objects.get(title='The Burning Awesome')
    tba_band.delete()
except Band.DoesNotExist:
    pass

# create the band
tba_band = Band()
tba_band.date_created = '2008-03-14 00:00:00'
tba_band.title = "The Burning Awesome"
tba_band.url = 'the_burning_awesome'
tba_band.openness = Band.PRIVATE
tba_band.concurrent_editing = False
tba_band.total_space = 1024 * 1024 * 1024 * 5 # just give a nice buffer. we can change it later.
tba_band.used_space = 0
tba_band._save()

# create band members
BandMember.objects.create(user=andy, band=tba_band, role=BandMember.MANAGER, space_donated=0)
BandMember.objects.create(user=tyler, band=tba_band, role=BandMember.BAND_MEMBER, space_donated=0)
BandMember.objects.create(user=casey, band=tba_band, role=BandMember.BAND_MEMBER, space_donated=0)

def add_version_comments(old_project, old_version, project, version):
    # add each version comment in order
    this_comments = filter(lambda x: x['fields']['project_version'] == old_version['pk'], comments.values())
    this_comments.sort(key=lambda x: x['pk'])

    for old_comment in this_comments:
        parent = version.song.comment_node
        content = old_comment['fields']['content']
        old_owner_id = old_comment['fields']['author']
        if not tba_prof_to_sc_user.has_key(old_owner_id):
            continue
        owner = tba_prof_to_sc_user[old_owner_id]

        node = SongCommentNode()
        node.song = parent.song
        node.parent = parent
        node.owner = owner
        node.content = content
        node.position = None
        node.reply_disabled = False
        node.save()
        node.date_created = old_comment['fields']['date_posted']
        node.date_edited = old_comment['fields']['date_edited']
        node._save()

# for each first version
i = 0
count = len(first_versions)
for version_id, old_version in first_versions.iteritems():
    i += 1
    old_project = projects[old_version['fields']['project']]
    if old_project['pk'] in skip_projects:
        print("Skipping {0}".format(old_project['pk']))
        continue
    print("({0}/{1}) Importing {2}".format(i, count, old_project['fields']['title']))
    print(" - version 1")

    # create the first version
    owner = tba_prof_to_sc_user[old_version['fields']['owner']]
    result = upload_song(owner,
        file_mp3_handle=open_file(old_version['fields']['mp3_preview']),
        file_source_handle=open_file(old_version['fields']['file']),
        band=tba_band,
        song_title=old_project['fields']['title'],
        song_comments=old_version['fields']['comments'],
        filename_appendix="_1")
    if not result['success']:
        if result['reason'] in (design.invalid_mp3_file, design.sketchy_mp3_file, design.unable_to_save_id3_tags):
            # don't upload mp3
            result = upload_song(owner,
                file_mp3_handle=None,
                file_source_handle=open_file(old_version['fields']['file']),
                band=tba_band,
                song_title=old_project['fields']['title'],
                song_comments=old_version['fields']['comments'],
                filename_appendix="_1")
        else:
            print("ERROR: {0}".format(result['reason']))
            break

    # fill in the rest of the fields
    song = result['song']
    song.save()

    # create the project
    project = Project()
    project.band = tba_band
    project.visible = old_project['fields']['visible']
    if old_project['fields']['checked_out']:
        project.checked_out_to = tba_prof_to_sc_user[old_project['fields']['checked_out_to']]
    project.save()

    # create the first version
    version = ProjectVersion()
    version.project = project
    version.song = song
    version.version = 1
    version.saveNewVersion()

    # subscribe the creator
    project.subscribers.add(owner)
    project.save()
    add_version_comments(old_project, old_version, project, version)

    # add each version in order
    this_versions = filter(lambda v: v['fields']['project'] == old_project['pk'], versions.values())
    this_versions.sort(key=lambda x: x['pk'])
    for old_version in this_versions:
        owner = tba_prof_to_sc_user[old_version['fields']['owner']]
        new_version_number = old_version['fields']['version']
        print(" - version {0}".format(new_version_number))
        filename_appendix = "_" + str(new_version_number)
        result = upload_song(owner,
            file_mp3_handle=open_file(old_version['fields']['mp3_preview']),
            file_source_handle=open_file(old_version['fields']['file']),
            band=tba_band,
            song_title=old_project['fields']['title'],
            song_comments=old_version['fields']['comments'],
            filename_appendix=filename_appendix)
        if not result['success']:
            if result['reason'] in (design.invalid_mp3_file, design.sketchy_mp3_file, design.unable_to_save_id3_tags):
                result = upload_song(owner,
                    file_mp3_handle=None,
                    file_source_handle=open_file(old_version['fields']['file']),
                    band=tba_band,
                    song_title=old_project['fields']['title'],
                    song_comments=old_version['fields']['comments'],
                    filename_appendix=filename_appendix)
            else:
                print("ERROR: {0}".format(result['reason']))
                # just skip this one
                continue

        song = result['song']
        song.save()

        # make a new version
        version = ProjectVersion()
        version.project = project
        version.song = song
        version.version = new_version_number
        version.saveNewVersion()
        version.date_added = old_version['fields']['version_date']
        version._save()

        # update project info
        project.checked_out_to = None
        project.latest_version = version
        project.title = song.title
        project.save()

        add_version_comments(old_project, old_version, project, version)

    project.date_activity = old_project['fields']['date_activity']
    project._save()

