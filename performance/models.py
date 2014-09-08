#  Copyright 2008-2014 Xiang Liu (liu980299@gmail.com)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from django.db import models 

class Application(models.Model):
	app_name = models.CharField(max_length = 64)
	app_description = models.TextField(max_length=1024)
	
class Module(models.Model):
	module_name = models.CharField(max_length=64)
	module_threads = models.PositiveSmallIntegerField()
	module_ramp_up = models.PositiveSmallIntegerField()
	module_loop = models.PositiveSmallIntegerField()
	module_target = models.CharField(max_length=1024)
	module_testplan = models.CharField(max_length=1024)
	module_data = models.CharField(max_length=1024)
	application = models.ForeignKey(Application)

class Scenario(models.Model):
	scenario_name = models.CharField(max_length=64)
	scenario_description = models.TextField(default="Scenario description", max_length=1024)
	scenario_data = models.CharField(max_length=1024)
	module = models.ForeignKey(Module)
	
class TestRun(models.Model):
	func_name = models.CharField(max_length=64)
	timestamp = models.DateTimeField(auto_now=True)
	ts_string = models.CharField(max_length=64)
	target = models.CharField(max_length=1024)
	result = models.CharField(max_length=64, null = True)
	message = models.CharField(max_length=64,null = True)
	module = models.ForeignKey(Module)
	
class TestReport(models.Model):
	func_name = models.CharField(max_length=64)
	sample_name = models.CharField(max_length=256)
	response_time = models.PositiveIntegerField()
	URL = models.CharField(max_length=2048)
	running_time = models.DateTimeField()
	response_code = models.PositiveSmallIntegerField()
	timestamp = models.DateTimeField(auto_now=True)
	ts_string = models.CharField(max_length=64)
	target = models.CharField(max_length=1024)
	result = models.CharField(max_length=64, null = True)
	message = models.CharField(max_length=64,null = True)
	scenario = models.ForeignKey(Scenario)