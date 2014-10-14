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
	def __str__(self):
		return self.app_name
	
class Module(models.Model):
	module_name = models.CharField(max_length=64)
	module_threads = models.PositiveSmallIntegerField()
	module_ramp_up = models.PositiveSmallIntegerField()
	module_loop = models.PositiveSmallIntegerField()
	module_target = models.CharField(max_length=1024)
	module_testplan = models.CharField(max_length=1024)
	module_data = models.CharField(max_length=1024)
	application = models.ForeignKey(Application)
	def __str__(self):
		return self.module_name
		
	
class Function(models.Model):
	func_name = models.CharField(max_length=64)
	func_setting = models.CharField(max_length=2048)
	module = models.ForeignKey(Module)
	def __str__(self):
		return self.func_name

class Scenario(models.Model):
	scenario_name = models.CharField(max_length=64)
	scenario_description = models.TextField(default="Scenario description", max_length=1024)
	scenario_data = models.CharField(max_length=1024)
	scenario_header = models.CharField(max_length=2048)
	module = models.ForeignKey(Module, null=True)
	function = models.ForeignKey(Function,null=True)
	def __str__(self):
		return self.function.func_name + "_" + self.scenario_name
	
class TestRun(models.Model):
	func_name = models.CharField(max_length=64)
	timestamp = models.DateTimeField(auto_now=True)
	ts_string = models.CharField(max_length=64)
	target = models.CharField(max_length=1024)
	result = models.CharField(max_length=64, null = True)
	message = models.CharField(max_length=64,null = True)
	module = models.ForeignKey(Module)

class Tag(models.Model):
	tag_name = models.CharField(max_length=64)
	tag_description = models.CharField(max_length=2048)
	
	def __str__(self):
		return self.tag_name	
	
class Sample(models.Model):
	sample_name = models.CharField(max_length=64)
	priority = models.PositiveIntegerField()
	sample_value = models.TextField()
	scenario = models.ForeignKey(Scenario)
	is_deleted = models.CharField(max_length=1)	
	tags = models.ManyToManyField(Tag)
	
class TestReport(models.Model):
	func_name = models.CharField(max_length=64)
	sample_name = models.CharField(max_length=256)
	response_time = models.PositiveIntegerField()
	URL = models.CharField(max_length=2048)
	response_code = models.CharField(max_length=1024,null = True)
	timestamp = models.CharField(max_length=64)
	ts_string = models.CharField(max_length=64)
	type = models.CharField(max_length=64)
	thread_name = models.CharField(max_length=256)
	bytes = models.PositiveIntegerField()
	latency = models.PositiveIntegerField()
	target = models.CharField(max_length=1024)
	result = models.CharField(max_length=64, null = True)
	message = models.CharField(max_length=1024,null = True)
	sample = models.ForeignKey(Sample)	
	
	def JMeterDict(self):
		res = {}
		res['Sample Name'] = self.sample_name
		res['Result'] = self.result
		res['Response Message'] = self.message
		res['Latency'] = self.latency
		res['Type'] = self.type
		res['Bytes'] = self.bytes
		res['Time Stamp'] = self.timestamp
		res['Response Time'] = self.response_time
		res['Response Code'] = self.response_code
		res['URL'] = self.URL
		res['Thread Name'] = self.thread_name
		res['Priority'] = self.sample.priority
		return res

	
class Fields(models.Model):
	field_name = models.CharField(max_length=64)
	field_value = models.CharField(max_length=2048)
	field_type = models.CharField(max_length=64)
	sample = models.ForeignKey(Sample)
	is_deleted = models.CharField(max_length=1)
	
