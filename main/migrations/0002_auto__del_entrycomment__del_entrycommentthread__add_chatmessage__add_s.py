# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting model 'EntryComment'
        db.delete_table('main_entrycomment')

        # Deleting model 'EntryCommentThread'
        db.delete_table('main_entrycommentthread')

        # Adding model 'ChatMessage'
        db.create_table('main_chatmessage', (
            ('room', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ChatRoom'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'], null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['ChatMessage'])

        # Adding model 'SongComment'
        db.create_table('main_songcomment', (
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_edited', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['SongComment'])

        # Adding model 'SongCommentThread'
        db.create_table('main_songcommentthread', (
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Entry'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('position', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['SongCommentThread'])

        # Adding model 'Song'
        db.create_table('main_song', (
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('mp3_file', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('waveform_img', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('length', self.gf('django.db.models.fields.FloatField')()),
            ('source_file', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['Song'])

        # Adding model 'ChatRoom'
        db.create_table('main_chatroom', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('permission_type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('main', ['ChatRoom'])

        # Adding M2M table for field blacklist on 'ChatRoom'
        db.create_table('main_chatroom_blacklist', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('chatroom', models.ForeignKey(orm['main.chatroom'], null=False)),
            ('profile', models.ForeignKey(orm['main.profile'], null=False))
        ))
        db.create_unique('main_chatroom_blacklist', ['chatroom_id', 'profile_id'])

        # Adding M2M table for field whitelist on 'ChatRoom'
        db.create_table('main_chatroom_whitelist', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('chatroom', models.ForeignKey(orm['main.chatroom'], null=False)),
            ('profile', models.ForeignKey(orm['main.profile'], null=False))
        ))
        db.create_unique('main_chatroom_whitelist', ['chatroom_id', 'profile_id'])

        # Deleting field 'Entry.mp3_file'
        db.delete_column('main_entry', 'mp3_file')

        # Deleting field 'Entry.length'
        db.delete_column('main_entry', 'length')

        # Deleting field 'Entry.source_file'
        db.delete_column('main_entry', 'source_file')

        # Adding field 'Entry.submit_date'
        db.add_column('main_entry', 'submit_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2010, 4, 27, 3, 2, 46, 232116), blank=True), keep_default=False)

        # Adding field 'Entry.song'
        db.add_column('main_entry', 'song', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['main.Song']), keep_default=False)

        # Adding field 'Competition.chat_room'
        db.add_column('main_competition', 'chat_room', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['main.ChatRoom']), keep_default=False)
    
    
    def backwards(self, orm):
        
        # Adding model 'EntryComment'
        db.create_table('main_entrycomment', (
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('date_edited', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('main', ['EntryComment'])

        # Adding model 'EntryCommentThread'
        db.create_table('main_entrycommentthread', (
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Entry'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('position', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['EntryCommentThread'])

        # Deleting model 'ChatMessage'
        db.delete_table('main_chatmessage')

        # Deleting model 'SongComment'
        db.delete_table('main_songcomment')

        # Deleting model 'SongCommentThread'
        db.delete_table('main_songcommentthread')

        # Deleting model 'Song'
        db.delete_table('main_song')

        # Deleting model 'ChatRoom'
        db.delete_table('main_chatroom')

        # Removing M2M table for field blacklist on 'ChatRoom'
        db.delete_table('main_chatroom_blacklist')

        # Removing M2M table for field whitelist on 'ChatRoom'
        db.delete_table('main_chatroom_whitelist')

        # Adding field 'Entry.mp3_file'
        db.add_column('main_entry', 'mp3_file', self.gf('django.db.models.fields.CharField')(default='', max_length=500), keep_default=False)

        # Adding field 'Entry.length'
        db.add_column('main_entry', 'length', self.gf('django.db.models.fields.FloatField')(default=0), keep_default=False)

        # Adding field 'Entry.source_file'
        db.add_column('main_entry', 'source_file', self.gf('django.db.models.fields.CharField')(default='', max_length=500), keep_default=False)

        # Deleting field 'Entry.submit_date'
        db.delete_column('main_entry', 'submit_date')

        # Deleting field 'Entry.song'
        db.delete_column('main_entry', 'song_id')

        # Deleting field 'Competition.chat_room'
        db.delete_column('main_competition', 'chat_room_id')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.chatmessage': {
            'Meta': {'object_name': 'ChatMessage'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'room': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ChatRoom']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'main.chatroom': {
            'Meta': {'object_name': 'ChatRoom'},
            'blacklist': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'blacklisted_users'", 'to': "orm['main.Profile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission_type': ('django.db.models.fields.IntegerField', [], {}),
            'whitelist': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'whitelisted_users'", 'to': "orm['main.Profile']"})
        },
        'main.competition': {
            'Meta': {'object_name': 'Competition'},
            'chat_room': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ChatRoom']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'have_listening_party': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'listening_party_end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'listening_party_start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'preview_rules': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'preview_theme': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'rules': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'submit_deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'theme': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'vote_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'vote_period_length': ('django.db.models.fields.IntegerField', [], {})
        },
        'main.entry': {
            'Meta': {'object_name': 'Entry'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Competition']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"}),
            'song': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Song']"}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'main.profile': {
            'Meta': {'object_name': 'Profile'},
            'activate_code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'activated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'artist_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'competitions_bookmarked': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'competitions_bookmarked'", 'blank': 'True', 'to': "orm['main.Competition']"}),
            'date_activity': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logon_count': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'main.song': {
            'Meta': {'object_name': 'Song'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.FloatField', [], {}),
            'mp3_file': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"}),
            'source_file': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'waveform_img': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        'main.songcomment': {
            'Meta': {'object_name': 'SongComment'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_edited': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"})
        },
        'main.songcommentthread': {
            'Meta': {'object_name': 'SongCommentThread'},
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Entry']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.FloatField', [], {})
        },
        'main.thumbsup': {
            'Meta': {'object_name': 'ThumbsUp'},
            'date_given': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Entry']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"})
        }
    }
    
    complete_apps = ['main']
