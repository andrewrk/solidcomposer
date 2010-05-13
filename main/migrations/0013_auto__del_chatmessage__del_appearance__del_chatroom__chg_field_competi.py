# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting model 'ChatMessage'
        db.delete_table('main_chatmessage')

        # Deleting model 'Appearance'
        db.delete_table('main_appearance')

        # Deleting model 'ChatRoom'
        db.delete_table('main_chatroom')

        # Removing M2M table for field blacklist on 'ChatRoom'
        db.delete_table('main_chatroom_blacklist')

        # Removing M2M table for field whitelist on 'ChatRoom'
        db.delete_table('main_chatroom_whitelist')

        # Changing field 'Competition.chat_room'
        db.alter_column('main_competition', 'chat_room_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chat.ChatRoom'], null=True, blank=True))
    
    
    def backwards(self, orm):
        
        # Adding model 'ChatMessage'
        db.create_table('main_chatmessage', (
            ('room', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ChatRoom'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'], null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['ChatMessage'])

        # Adding model 'Appearance'
        db.create_table('main_appearance', (
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('room', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ChatRoom'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['Appearance'])

        # Adding model 'ChatRoom'
        db.create_table('main_chatroom', (
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
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

        # Changing field 'Competition.chat_room'
        db.alter_column('main_competition', 'chat_room_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.ChatRoom'], null=True, blank=True))
    
    
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
        'chat.chatroom': {
            'Meta': {'object_name': 'ChatRoom'},
            'blacklist': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'blacklisted_users'", 'null': 'True', 'to': "orm['auth.User']"}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission_type': ('django.db.models.fields.IntegerField', [], {}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'whitelist': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'whitelisted_users'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.competition': {
            'Meta': {'object_name': 'Competition'},
            'chat_room': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chat.ChatRoom']", 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'have_listening_party': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'listening_party_end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'listening_party_start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'preview_rules': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'preview_theme': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'rules': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {}),
            'submit_deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'theme': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'vote_deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'vote_period_length': ('django.db.models.fields.IntegerField', [], {})
        },
        'main.entry': {
            'Meta': {'object_name': 'Entry'},
            'competition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Competition']"}),
            'edit_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"}),
            'song': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Song']"}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'main.profile': {
            'Meta': {'object_name': 'Profile'},
            'activate_code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'activated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'artist_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'competitions_bookmarked': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'competitions_bookmarked'", 'blank': 'True', 'to': "orm['main.Competition']"}),
            'date_activity': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'main.song': {
            'Meta': {'object_name': 'Song'},
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.FloatField', [], {}),
            'mp3_file': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"}),
            'source_file': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'waveform_img': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'})
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
