# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TestReport'
        db.create_table(u'performance_testreport', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('func_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('sample_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('response_time', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('URL', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('response_code', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('timestamp', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('ts_string', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('thread_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('bytes', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('latency', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('target', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('result', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('sample', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['performance.Sample'])),
        ))
        db.send_create_signal(u'performance', ['TestReport'])


    def backwards(self, orm):
        # Deleting model 'TestReport'
        db.delete_table(u'performance_testreport')


    models = {
        u'performance.application': {
            'Meta': {'object_name': 'Application'},
            'app_description': ('django.db.models.fields.TextField', [], {'max_length': '1024'}),
            'app_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'performance.fields': {
            'Meta': {'object_name': 'Fields'},
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'field_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'field_value': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'sample': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Sample']"})
        },
        u'performance.module': {
            'Meta': {'object_name': 'Module'},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Application']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module_data': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'module_loop': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'module_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'module_ramp_up': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'module_target': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'module_testplan': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'module_threads': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'performance.sample': {
            'Meta': {'object_name': 'Sample'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sample_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'sample_value': ('django.db.models.fields.TextField', [], {}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Scenario']"})
        },
        u'performance.scenario': {
            'Meta': {'object_name': 'Scenario'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Module']"}),
            'scenario_data': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'scenario_description': ('django.db.models.fields.TextField', [], {'default': "'Scenario description'", 'max_length': '1024'}),
            'scenario_header': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'scenario_name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'performance.testreport': {
            'Meta': {'object_name': 'TestReport'},
            'URL': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'bytes': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'func_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latency': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'response_code': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'response_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'sample': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Sample']"}),
            'sample_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'thread_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'timestamp': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'ts_string': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'performance.testrun': {
            'Meta': {'object_name': 'TestRun'},
            'func_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Module']"}),
            'result': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'ts_string': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['performance']