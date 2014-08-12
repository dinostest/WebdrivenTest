# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Application'
        db.create_table(u'performance_application', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('app_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('app_description', self.gf('django.db.models.fields.TextField')(max_length=1024)),
        ))
        db.send_create_signal(u'performance', ['Application'])

        # Adding model 'Module'
        db.create_table(u'performance_module', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('module_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('module_threads', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('module_ramp_up', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('module_loop', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('module_target', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('module_testplan', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('module_data', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('application', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['performance.Application'])),
        ))
        db.send_create_signal(u'performance', ['Module'])

        # Adding model 'Scenario'
        db.create_table(u'performance_scenario', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('scenario_data', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['performance.Module'])),
        ))
        db.send_create_signal(u'performance', ['Scenario'])


    def backwards(self, orm):
        # Deleting model 'Application'
        db.delete_table(u'performance_application')

        # Deleting model 'Module'
        db.delete_table(u'performance_module')

        # Deleting model 'Scenario'
        db.delete_table(u'performance_scenario')


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
            'scenario_name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['performance']