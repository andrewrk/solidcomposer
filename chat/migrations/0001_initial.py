# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'ChatRoom'
        db.create_table('chat_chatroom', (
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('permission_type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('chat', ['ChatRoom'])

        # Adding M2M table for field blacklist on 'ChatRoom'
        db.create_table('chat_chatroom_blacklist', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('chatroom', models.ForeignKey(orm['chat.chatroom'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('chat_chatroom_blacklist', ['chatroom_id', 'user_id'])

        # Adding M2M table for field whitelist on 'ChatRoom'
        db.create_table('chat_chatroom_whitelist', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('chatroom', models.ForeignKey(orm['chat.chatroom'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('chat_chatroom_whitelist', ['chatroom_id', 'user_id'])

        # Adding model 'ChatMessage'
        db.create_table('chat_chatmessage', (
            ('room', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chat.ChatRoom'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('chat', ['ChatMessage'])

        # Adding model 'Appearance'
        db.create_table('chat_appearance', (
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('room', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chat.ChatRoom'])),
        ))
        db.send_create_signal('chat', ['Appearance'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'ChatRoom'
        db.delete_table('chat_chatroom')

        # Removing M2M table for field blacklist on 'ChatRoom'
        db.delete_table('chat_chatroom_blacklist')

        # Removing M2M table for field whitelist on 'ChatRoom'
        db.delete_table('chat_chatroom_whitelist')

        # Deleting model 'ChatMessage'
        db.delete_table('chat_chatmessage')

        # Deleting model 'Appearance'
        db.delete_table('chat_appearance')
    
    
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
        'chat.appearance': {
            'Meta': {'object_name': 'Appearance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'room': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chat.ChatRoom']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'chat.chatmessage': {
            'Meta': {'object_name': 'ChatMessage'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'room': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chat.ChatRoom']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
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
        }
    }
    
    complete_apps = ['chat']
