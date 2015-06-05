#  Copyright Xiang Liu (liu980299@gmail.com)
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
from performance.models import Function,TestRun,TestReport
import json

class Environment(models.Model):
	name = models.CharField(max_length = 64)
	description = models.TextField(max_length=1024)
	portal = models.CharField(max_length = 1024, null=True)	
	setting = models.CharField(max_length = 1024, null=True) 
	isDeleted = models.CharField(max_length = 1,default='N')
	
class Server(models.Model):
	hostname = models.TextField(max_length=1024)
	type = models.CharField(max_length = 64, null=True)
	memory = models.PositiveSmallIntegerField(null=True)
	cpu = models.TextField(max_length = 2048, null=True)
	def __str__(self):
		return self.hostname

class Service(models.Model):
	name = models.CharField(max_length = 1024)
	description = models.TextField(max_length=2048)
	hostname = models.TextField(max_length=1024)
	port = models.PositiveSmallIntegerField()
	url = models.CharField(max_length = 1024, null=True)
	logfile = models.CharField(max_length = 1024,null=True)
	type = models.CharField(max_length = 64, null=True)
	monitored = models.BooleanField(default = False)
	pslocator = models.TextField(max_length=1024,null=True)
	monitor_script = models.TextField(max_length=1024,null=True)
	isDeleted = models.CharField(max_length = 1,default='N')
	environment = models.ForeignKey(Environment)
	server = models.ForeignKey(Server)
	def __str__(self):
		return self.name

class Monitor(models.Model):
	name = models.CharField(max_length = 1024)
	headerscript = models.TextField(max_length = 2048)
	pidscript = models.TextField(max_length = 2048)
	script = models.TextField(max_length = 2048)
	server = models.ManyToManyField(Server)
	def __str__(self):
		return self.name

class ServiceMonitor(models.Model):		
	name = models.CharField(max_length = 1024)
	script = models.TextField(max_length = 2048)
	service = models.ForeignKey(Service)
	def __str__(self):
		return self.name
			
class Job(models.Model):
	name = models.CharField(max_length = 1024)
	description = models.TextField(max_length=2048)
	autocompleted = models.BooleanField(default = False)
	pattern = models.CharField(max_length = 512, null=True)
	value = models.CharField(max_length = 1024, null=True)
	function = models.ForeignKey(Function)
	def __str__(self):
		return self.name
	
class JobService(models.Model):
	name = models.CharField(max_length = 1024)
	description = models.TextField(max_length=2048)
	sequence = models.PositiveSmallIntegerField()
	service = models.ForeignKey(Service)
	starttime = models.CharField(max_length = 128)
	endtime = models.CharField(max_length = 128)
	pattern = models.CharField(max_length = 512, null=True)
	job = models.ForeignKey(Job)
	def __str__(self):
		return self.name
	
	
class JobRun(models.Model):
	ts_string = models.CharField(max_length=64)
	job = models.ForeignKey(Job)
	environment = models.ForeignKey(Environment)
	value = models.CharField(max_length = 1024, null=True)
	status = models.CharField(max_length = 64, null=True)
	testreport = models.ForeignKey(TestReport)
	testrun = models.ForeignKey(TestRun)

class ServiceRun(models.Model):
	startline = models.PositiveIntegerField()
	endline = models.PositiveIntegerField()
	message = models.TextField(max_length=4096)
	service = models.ForeignKey(Service)
	testrun = models.ForeignKey(TestRun)

class MonitorRun(models.Model):
	starttime = models.DateTimeField()
	endtime = models.DateTimeField()
	header = models.CharField(max_length = 1024, null=True)
	pid = models.CharField(max_length = 64, null=True)
	monitor = models.ForeignKey(Monitor)
	server = models.ForeignKey(Server, null=True)
	testrun = models.ForeignKey(TestRun)
		
	
class JobServiceResult(models.Model):
	processtime = models.PositiveIntegerField(null=True)
	starttime = models.CharField(max_length = 128)
	endtime = models.CharField(max_length = 128)
	value = models.CharField(max_length=256)
	status = models.CharField(max_length=64)
	servicerun = models.ForeignKey(ServiceRun)
	jobrun = models.ForeignKey(JobRun)
	jobservice = models.ForeignKey(JobService)
	def getDict(self):
		res = {}
		res["Start Time"] = self.starttime
		res["End Time"] = self.endtime
		res["value"] = json.loads(self.value)
		res["Status"] = self.status
		res["Process Time"] = self.processtime
		return res
	
class HubCfg(models.Model):
	name = models.CharField(max_length = 64)
	description = models.TextField(max_length=1024)
	value = models.CharField(max_length = 64)
	type = models.CharField(max_length = 64)
	isDeleted = models.CharField(max_length = 64)
	
class Machine(models.Model):
	hostname = models.CharField(max_length = 64)
	ipaddr = models.CharField(max_length = 64)
	maxSession = models.PositiveSmallIntegerField()
	role = models.CharField(max_length = 64)
	registerCycle = models.PositiveSmallIntegerField()
	url = models.CharField(max_length = 1024)
	remoteHost = models.CharField(max_length = 1024)
	OS = models.CharField(max_length = 64)
	version = models.CharField(max_length = 64)

class Browser(models.Model):
	browsername = models.CharField(max_length = 64)
	version = models.CharField(max_length = 64)
	maxInstances = models.PositiveSmallIntegerField()
	platform = models.CharField(max_length = 64)
	machine = models.ForeignKey(Machine)
	