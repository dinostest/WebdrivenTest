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
	name = models.CharField(max_length = 64)
	description = models.TextField(max_length=1024)
	is_deleted = models.CharField(max_length=1,default='N')
	def __str__(self):
		return self.name
	
class Module(models.Model):
	name = models.CharField(max_length=64)
	description = models.TextField(max_length=1024)
	is_deleted = models.CharField(max_length=1,default='N')
	application = models.ForeignKey(Application)
	def __str__(self):
		return self.name
		
	
class Function(models.Model):
	name = models.CharField(max_length=64)
	description = models.CharField(max_length=2048)
	is_deleted = models.CharField(max_length=1,default='N')
	module = models.ForeignKey(Module)
	def __str__(self):
		return self.name

class Scenario(models.Model):
	name = models.CharField(max_length=64)
	target = models.CharField(max_length=1024, default="N/A")
	description = models.TextField(default="description", max_length=1024)
	resource = models.TextField(default="", max_length=1024)
	settings = models.CharField(max_length=2048)
	script = models.CharField(max_length=1024)
	sample_header = models.CharField(max_length=2048)
	is_deleted = models.CharField(max_length=1,default='N')
	func = models.ForeignKey(Function)
	def __str__(self):
		return self.func.name + "_" + self.name

class Gherkins_keyword(models.Model):
	name = models.CharField(max_length=1024)
	args = models.CharField(max_length=2048)
	is_deleted = models.CharField(max_length=1,default='N')
	line_no = models.PositiveIntegerField(null = True)
	scenario = models.ForeignKey(Scenario)

class Browser(models.Model):
	type = models.CharField(max_length=64)
	version = models.CharField(max_length=64)
	isActive = models.CharField(max_length=1)

class TestMachine(models.Model):
	label = models.CharField(max_length=64)
	hostname = models.CharField(max_length=64)
	platform = models.CharField(max_length=64)
	browsers = models.ManyToManyField(Browser)
	
class TestRun(models.Model):
	level = models.CharField(max_length=64)
	name = models.CharField(max_length=64)
	timestamp = models.DateTimeField(auto_now=True)
	ts_string = models.CharField(max_length=64)
	target = models.CharField(max_length=1024)
	result = models.CharField(max_length=64, null = True)
	message = models.CharField(max_length=64,null = True)
	scenario = models.ForeignKey(Scenario)
	machine = models.ForeignKey(TestMachine)

class Tag(models.Model):
	tag_name = models.CharField(max_length=64)
	tag_description = models.CharField(max_length=2048)
	
	def __str__(self):
		return self.tag_name	
	
class Sample(models.Model):
	name = models.CharField(max_length=64)
	priority = models.PositiveIntegerField()
	value = models.TextField()
	scenario = models.ForeignKey(Scenario)
	is_deleted = models.CharField(max_length=1)
	line_no = models.PositiveIntegerField(null = True)
	tags = models.ManyToManyField(Tag)
	
class TestReport(models.Model):
	suite_name = models.CharField(max_length=64)
	sample_name = models.CharField(max_length=256)
	timestamp = models.CharField(max_length=64)
	ts_string = models.CharField(max_length=64)
	type = models.CharField(max_length=64)
	duration = models.PositiveIntegerField()
	target = models.CharField(max_length=1024)
	result = models.CharField(max_length=64, null = True)
	message = models.CharField(max_length=1024,null = True)
	sample = models.ForeignKey(Sample)
	testrun = models.ForeignKey(TestRun)
	



