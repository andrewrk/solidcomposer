# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'ProjectVersion.new_title'
        db.add_column('workshop_projectversion', 'new_title', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True), keep_default=False)

        # Adding M2M table for field provided_samples on 'ProjectVersion'
        db.create_table('workshop_projectversion_provided_samples', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('projectversion', models.ForeignKey(orm['workshop.projectversion'], null=False)),
            ('uploadedsample', models.ForeignKey(orm['workshop.uploadedsample'], null=False))
        ))
        db.create_unique('workshop_projectversion_provided_samples', ['projectversion_id', 'uploadedsample_id'])

        # Changing field 'ProjectVersion.song'
        db.alter_column('workshop_projectversion', 'song_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Song'], null=True, blank=True))


    def backwards(self, orm):
        
        # Deleting field 'ProjectVersion.new_title'
        db.delete_column('workshop_projectversion', 'new_title')

        # Removing M2M table for field provided_samples on 'ProjectVersion'
        db.delete_table('workshop_projectversion_provided_samples')

        # Changing field 'ProjectVersion.song'
        db.alter_column('workshop_projectversion', 'song_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Song']))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.band': {
            'Meta': {'object_name': 'Band'},
            'abandon_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'bio': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'concurrent_editing': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'openness': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'total_space': ('django.db.models.fields.BigIntegerField', [], {}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '110', 'unique': 'True', 'null': 'True'}),
            'used_space': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
        },
        'main.song': {
            'Meta': {'object_name': 'Song'},
            'album': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']"}),
            'comment_node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'song_comment_node'", 'null': 'True', 'to': "orm['main.SongCommentNode']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_open_source': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'length': ('django.db.models.fields.FloatField', [], {}),
            'mp3_file': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'plugins': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'song_plugins'", 'blank': 'True', 'to': "orm['workshop.PluginDepenency']"}),
            'source_file': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'studio': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workshop.Studio']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'waveform_img': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'})
        },
        'main.songcommentnode': {
            'Meta': {'object_name': 'SongCommentNode'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {}),
            'date_edited': ('django.db.models.fields.DateTimeField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.SongCommentNode']", 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'reply_disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'song': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Song']"})
        },
        'main.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'workshop.bandinvitation': {
            'Meta': {'object_name': 'BandInvitation'},
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'expire_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitee': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'invitee'", 'null': 'True', 'to': "orm['auth.User']"}),
            'inviter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'inviter'", 'to': "orm['auth.User']"}),
            'role': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        'workshop.plugindepenency': {
            'Meta': {'object_name': 'PluginDepenency'},
            'comes_with_studio': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workshop.Studio']", 'null': 'True', 'blank': 'True'}),
            'external_url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'plugin_type': ('django.db.models.fields.IntegerField', [], {}),
            'price': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'workshop.project': {
            'Meta': {'object_name': 'Project'},
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']"}),
            'checked_out_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'checked_out_to'", 'null': 'True', 'to': "orm['auth.User']"}),
            'date_activity': ('django.db.models.fields.DateTimeField', [], {}),
            'forked_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'forked_from'", 'null': 'True', 'to': "orm['workshop.ProjectVersion']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest_version': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'latest_version'", 'null': 'True', 'to': "orm['workshop.ProjectVersion']"}),
            'merged_from': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'merged_from'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['workshop.ProjectVersion']"}),
            'promote_voters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'promote_voters'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'scrap_voters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'scrap_voters'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'project_subscribers'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'})
        },
        'workshop.projectversion': {
            'Meta': {'object_name': 'ProjectVersion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workshop.Project']"}),
            'provided_samples': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'provided_samples'", 'blank': 'True', 'to': "orm['workshop.UploadedSample']"}),
            'song': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Song']", 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        'workshop.sampledependency': {
            'Meta': {'object_name': 'SampleDependency'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'song': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Song']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'uploaded_sample': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workshop.UploadedSample']", 'null': 'True', 'blank': 'True'})
        },
        'workshop.samplefile': {
            'Meta': {'object_name': 'SampleFile'},
            'hex_digest': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'workshop.studio': {
            'Meta': {'object_name': 'Studio'},
            'canMerge': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'canReadFile': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'canRender': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'external_url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'logo_16x16': ('django.db.models.fields.files.ImageField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'logo_large': ('django.db.models.fields.files.ImageField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'workshop.uploadedsample': {
            'Meta': {'object_name': 'UploadedSample'},
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sample_file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workshop.SampleFile']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['workshop']
