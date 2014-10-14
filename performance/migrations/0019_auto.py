# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing M2M table for field samples on 'Tag'
        db.delete_table(db.shorten_name(u'performance_tag_samples'))

        # Adding M2M table for field tags on 'Sample'
        m2m_table_name = db.shorten_name(u'performance_sample_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sample', models.ForeignKey(orm[u'performance.sample'], null=False)),
            ('tag', models.ForeignKey(orm[u'performance.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['sample_id', 'tag_id'])


    def backwards(self, orm):
        # Adding M2M table for field samples on 'Tag'
        m2m_table_name = db.shorten_name(u'performance_tag_samples')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tag', models.ForeignKey(orm[u'performance.tag'], null=False)),
            ('sample', models.ForeignKey(orm[u'performance.sample'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tag_id', 'sample_id'])

        # Removing M2M table for field tags on 'Sample'
        db.delete_table(db.shorten_name(u'performance_sample_tags'))


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
        u'performance.function': {
            'Meta': {'object_name': 'Function'},
            'func_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'func_setting': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Module']"})
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
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Scenario']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['performance.Tag']", 'symmetrical': 'False'})
        },
        u'performance.scenario': {
            'Meta': {'object_name': 'Scenario'},
            'function': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Function']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Module']", 'null': 'True'}),
            'scenario_data': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'scenario_description': ('django.db.models.fields.TextField', [], {'default': "'Scenario description'", 'max_length': '1024'}),
            'scenario_header': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'scenario_name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'performance.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag_description': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'tag_name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'performance.testreport': {
            'Meta': {'object_name': 'TestReport'},
            'URL': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'bytes': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'func_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latency': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'response_code': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
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