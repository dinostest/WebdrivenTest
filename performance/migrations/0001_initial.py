# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filter', models.CharField(max_length=512)),
                ('group', models.CharField(max_length=512)),
                ('brief', models.CharField(max_length=64)),
                ('func_name', models.CharField(max_length=64)),
                ('name', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app_name', models.CharField(max_length=64)),
                ('app_description', models.TextField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='Fields',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=64)),
                ('field_value', models.CharField(max_length=2048)),
                ('field_type', models.CharField(max_length=64)),
                ('is_deleted', models.CharField(max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Function',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('func_name', models.CharField(max_length=64)),
                ('func_setting', models.CharField(max_length=2048)),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('module_name', models.CharField(max_length=64)),
                ('module_threads', models.PositiveSmallIntegerField()),
                ('module_ramp_up', models.PositiveSmallIntegerField()),
                ('module_loop', models.PositiveSmallIntegerField()),
                ('module_target', models.CharField(max_length=1024)),
                ('module_testplan', models.CharField(max_length=1024)),
                ('module_data', models.CharField(max_length=1024)),
                ('application', models.ForeignKey(to='performance.Application')),
            ],
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=2048)),
            ],
        ),
        migrations.CreateModel(
            name='Sample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sample_name', models.CharField(max_length=64)),
                ('priority', models.PositiveIntegerField()),
                ('sample_value', models.TextField()),
                ('is_deleted', models.CharField(max_length=1)),
                ('line_no', models.PositiveIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scenario_name', models.CharField(max_length=64)),
                ('scenario_description', models.TextField(default=b'Scenario description', max_length=1024)),
                ('scenario_data', models.CharField(max_length=1024)),
                ('scenario_header', models.CharField(max_length=2048)),
                ('function', models.ForeignKey(to='performance.Function', null=True)),
                ('module', models.ForeignKey(to='performance.Module', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=512)),
                ('target', models.CharField(max_length=512)),
                ('setting', models.TextField(max_length=1024)),
                ('modifytime', models.DateTimeField(auto_now=True)),
                ('function', models.ForeignKey(to='performance.Function')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag_name', models.CharField(max_length=64)),
                ('tag_description', models.CharField(max_length=2048)),
                ('criteria', models.PositiveIntegerField(default=5000)),
            ],
        ),
        migrations.CreateModel(
            name='TestMachine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=64)),
                ('hostname', models.CharField(max_length=128)),
                ('username', models.CharField(max_length=128, null=True)),
                ('password', models.CharField(max_length=128, null=True)),
                ('jmeterpath', models.CharField(max_length=128, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TestPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.TextField(max_length=1024)),
                ('start_threads', models.PositiveIntegerField()),
                ('end_threads', models.PositiveIntegerField()),
                ('increment', models.PositiveIntegerField()),
                ('loops', models.PositiveIntegerField()),
                ('wait_time', models.PositiveIntegerField()),
                ('function', models.ForeignKey(to='performance.Function')),
            ],
        ),
        migrations.CreateModel(
            name='TestPlanRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.TextField(max_length=1024)),
                ('start_threads', models.PositiveIntegerField()),
                ('end_threads', models.PositiveIntegerField()),
                ('increment', models.PositiveIntegerField()),
                ('loops', models.PositiveIntegerField()),
                ('wait_time', models.PositiveIntegerField()),
                ('ts_string', models.CharField(max_length=64)),
                ('status', models.CharField(max_length=64)),
                ('testplan', models.ForeignKey(to='performance.TestPlan')),
            ],
        ),
        migrations.CreateModel(
            name='TestReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('func_name', models.CharField(max_length=64)),
                ('sample_name', models.CharField(max_length=256)),
                ('response_time', models.PositiveIntegerField()),
                ('URL', models.CharField(max_length=2048)),
                ('response_code', models.CharField(max_length=1024, null=True)),
                ('timestamp', models.CharField(max_length=64)),
                ('ts_string', models.CharField(max_length=64)),
                ('type', models.CharField(max_length=64)),
                ('thread_name', models.CharField(max_length=256)),
                ('bytes', models.PositiveIntegerField()),
                ('latency', models.PositiveIntegerField()),
                ('target', models.CharField(max_length=1024)),
                ('result', models.CharField(max_length=64, null=True)),
                ('message', models.CharField(max_length=1024, null=True)),
                ('sample', models.ForeignKey(to='performance.Sample')),
            ],
        ),
        migrations.CreateModel(
            name='TestRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256, null=True)),
                ('func_name', models.CharField(max_length=64)),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('ts_string', models.CharField(max_length=64)),
                ('target', models.CharField(max_length=1024)),
                ('result', models.CharField(max_length=64, null=True)),
                ('message', models.CharField(max_length=64, null=True)),
                ('priority', models.PositiveIntegerField()),
                ('threads', models.PositiveIntegerField(null=True)),
                ('loops', models.PositiveIntegerField(null=True)),
                ('wait_time', models.PositiveIntegerField(null=True)),
                ('fail_ratio', models.PositiveSmallIntegerField(null=True)),
                ('avg_response_time', models.PositiveIntegerField(null=True)),
                ('machine', models.ForeignKey(to='performance.TestMachine', null=True)),
                ('module', models.ForeignKey(to='performance.Module')),
                ('release', models.ForeignKey(to='performance.Release', null=True)),
                ('testplanrun', models.ForeignKey(to='performance.TestPlanRun', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='testreport',
            name='testrun',
            field=models.ForeignKey(to='performance.TestRun', null=True),
        ),
        migrations.AddField(
            model_name='sample',
            name='scenario',
            field=models.ForeignKey(to='performance.Scenario'),
        ),
        migrations.AddField(
            model_name='sample',
            name='tags',
            field=models.ManyToManyField(to='performance.Tag'),
        ),
        migrations.AddField(
            model_name='function',
            name='module',
            field=models.ForeignKey(to='performance.Module'),
        ),
        migrations.AddField(
            model_name='fields',
            name='sample',
            field=models.ForeignKey(to='performance.Sample'),
        ),
        migrations.AddField(
            model_name='analysis',
            name='module',
            field=models.ForeignKey(to='performance.Module'),
        ),
    ]
