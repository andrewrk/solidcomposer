# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'ProjectVersion'
        db.create_table('workshop_projectversion', (
            ('song', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Song'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['workshop.Project'])),
            ('version', self.gf('django.db.models.fields.IntegerField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('workshop', ['ProjectVersion'])

        # Adding model 'Project'
        db.create_table('workshop_project', (
            ('band', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Band'])),
            ('date_activity', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('forked_from', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='forked_from', null=True, to=orm['workshop.ProjectVersion'])),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('checked_out_to', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='checked_out_to', null=True, to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('can_check_out', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('workshop', ['Project'])

        # Adding M2M table for field promote_voters on 'Project'
        db.create_table('workshop_project_promote_voters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['workshop.project'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('workshop_project_promote_voters', ['project_id', 'user_id'])

        # Adding M2M table for field scrap_voters on 'Project'
        db.create_table('workshop_project_scrap_voters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['workshop.project'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('workshop_project_scrap_voters', ['project_id', 'user_id'])

        # Adding M2M table for field merged_from on 'Project'
        db.create_table('workshop_project_merged_from', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['workshop.project'], null=False)),
            ('projectversion', models.ForeignKey(orm['workshop.projectversion'], null=False))
        ))
        db.create_unique('workshop_project_merged_from', ['project_id', 'projectversion_id'])

        # Adding M2M table for field subscribers on 'Project'
        db.create_table('workshop_project_subscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['workshop.project'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('workshop_project_subscribers', ['project_id', 'user_id'])

        # Adding M2M table for field tags on 'Project'
        db.create_table('workshop_project_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['workshop.project'], null=False)),
            ('tag', models.ForeignKey(orm['main.tag'], null=False))
        ))
        db.create_unique('workshop_project_tags', ['project_id', 'tag_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'ProjectVersion'
        db.delete_table('workshop_projectversion')

        # Deleting model 'Project'
        db.delete_table('workshop_project')

        # Removing M2M table for field promote_voters on 'Project'
        db.delete_table('workshop_project_promote_voters')

        # Removing M2M table for field scrap_voters on 'Project'
        db.delete_table('workshop_project_scrap_voters')

        # Removing M2M table for field merged_from on 'Project'
        db.delete_table('workshop_project_merged_from')

        # Removing M2M table for field subscribers on 'Project'
        db.delete_table('workshop_project_subscribers')

        # Removing M2M table for field tags on 'Project'
        db.delete_table('workshop_project_tags')
    
    
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
        'main.band': {
            'Meta': {'object_name': 'Band'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'main.profile': {
            'Meta': {'object_name': 'Profile'},
            'activate_code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'activated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'competitions_bookmarked': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'competitions_bookmarked'", 'blank': 'True', 'to': "orm['main.Competition']"}),
            'date_activity': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'solo_band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']", 'unique': 'True'}),
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
        'main.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'workshop.project': {
            'Meta': {'object_name': 'Project'},
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']"}),
            'can_check_out': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'checked_out_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'checked_out_to'", 'null': 'True', 'to': "orm['auth.User']"}),
            'date_activity': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'forked_from': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'forked_from'", 'null': 'True', 'to': "orm['workshop.ProjectVersion']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merged_from': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'merged_from'", 'null': 'True', 'to': "orm['workshop.ProjectVersion']"}),
            'promote_voters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'promote_voters'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'scrap_voters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'scrap_voters'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'project_subscribers'", 'to': "orm['auth.User']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Tag']", 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'})
        },
        'workshop.projectversion': {
            'Meta': {'object_name': 'ProjectVersion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workshop.Project']"}),
            'song': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Song']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        }
    }
    
    complete_apps = ['workshop']
