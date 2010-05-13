# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'BandInvitation'
        db.create_table('workshop_bandinvitation', (
            ('count', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('invitee', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='invitee', null=True, to=orm['auth.User'])),
            ('band', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Band'])),
            ('role', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('expire_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('inviter', self.gf('django.db.models.fields.related.ForeignKey')(related_name='inviter', to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('workshop', ['BandInvitation'])

        # Deleting field 'Project.can_check_out'
        db.delete_column('workshop_project', 'can_check_out')
    
    
    def backwards(self, orm):
        
        # Deleting model 'BandInvitation'
        db.delete_table('workshop_bandinvitation')

        # Adding field 'Project.can_check_out'
        db.add_column('workshop_project', 'can_check_out', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)
    
    
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
        'main.band': {
            'Meta': {'object_name': 'Band'},
            'bio': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'concurrent_editing': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'openness': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.song': {
            'Meta': {'object_name': 'Song'},
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']"}),
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.FloatField', [], {}),
            'mp3_file': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'source_file': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'waveform_img': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'})
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
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'workshop.project': {
            'Meta': {'object_name': 'Project'},
            'band': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Band']"}),
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
