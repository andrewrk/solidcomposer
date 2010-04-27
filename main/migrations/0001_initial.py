# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Profile'
        db.create_table('main_profile', (
            ('logon_count', self.gf('django.db.models.fields.IntegerField')()),
            ('activated', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('date_activity', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('artist_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('activate_code', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['Profile'])

        # Adding M2M table for field competitions_bookmarked on 'Profile'
        db.create_table('main_profile_competitions_bookmarked', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('profile', models.ForeignKey(orm['main.profile'], null=False)),
            ('competition', models.ForeignKey(orm['main.competition'], null=False))
        ))
        db.create_unique('main_profile_competitions_bookmarked', ['profile_id', 'competition_id'])

        # Adding model 'Competition'
        db.create_table('main_competition', (
            ('have_listening_party', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('vote_deadline', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('rules', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('preview_rules', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('listening_party_start_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('theme', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('preview_theme', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('submit_deadline', self.gf('django.db.models.fields.DateTimeField')()),
            ('host', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('listening_party_end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vote_period_length', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('main', ['Competition'])

        # Adding model 'ThumbsUp'
        db.create_table('main_thumbsup', (
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Entry'])),
            ('date_given', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['ThumbsUp'])

        # Adding model 'Entry'
        db.create_table('main_entry', (
            ('mp3_file', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('competition', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Competition'])),
            ('length', self.gf('django.db.models.fields.FloatField')()),
            ('source_file', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['Entry'])

        # Adding model 'EntryCommentThread'
        db.create_table('main_entrycommentthread', (
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Entry'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('position', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('main', ['EntryCommentThread'])

        # Adding model 'EntryComment'
        db.create_table('main_entrycomment', (
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Profile'])),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_edited', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('main', ['EntryComment'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Profile'
        db.delete_table('main_profile')

        # Removing M2M table for field competitions_bookmarked on 'Profile'
        db.delete_table('main_profile_competitions_bookmarked')

        # Deleting model 'Competition'
        db.delete_table('main_competition')

        # Deleting model 'ThumbsUp'
        db.delete_table('main_thumbsup')

        # Deleting model 'Entry'
        db.delete_table('main_entry')

        # Deleting model 'EntryCommentThread'
        db.delete_table('main_entrycommentthread')

        # Deleting model 'EntryComment'
        db.delete_table('main_entrycomment')
    
    
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
        'main.competition': {
            'Meta': {'object_name': 'Competition'},
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
            'length': ('django.db.models.fields.FloatField', [], {}),
            'mp3_file': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"}),
            'source_file': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'main.entrycomment': {
            'Meta': {'object_name': 'EntryComment'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_edited': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"})
        },
        'main.entrycommentthread': {
            'Meta': {'object_name': 'EntryCommentThread'},
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Entry']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.FloatField', [], {})
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
        'main.thumbsup': {
            'Meta': {'object_name': 'ThumbsUp'},
            'date_given': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Entry']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Profile']"})
        }
    }
    
    complete_apps = ['main']
