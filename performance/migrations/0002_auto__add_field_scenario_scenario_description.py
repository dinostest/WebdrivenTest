# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Scenario.scenario_description'
        db.add_column(u'performance_scenario', 'scenario_description',
                      self.gf('django.db.models.fields.TextField')(default='test', max_length=1024),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Scenario.scenario_description'
        db.delete_column(u'performance_scenario', 'scenario_description')


    models = {
        u'performance.application': {
            'Meta': {'object_name': 'Application'},
            'app_description': ('django.db.models.fields.TextField', [], {'max_length': '1024'}),
            'app_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
        u'performance.scenario': {
            'Meta': {'object_name': 'Scenario'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['performance.Module']"}),
            'scenario_data': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'scenario_description': ('django.db.models.fields.TextField', [], {'default': "'test'", 'max_length': '1024'}),
            'scenario_name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['performance']