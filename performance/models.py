from django.db import models

# @Xiang Liu created for SAILIS project 

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
	result = models.CharField(max_length=64, null = True)
	message = models.CharField(max_length=64,null = True)
	module = models.ForeignKey(Module)
	