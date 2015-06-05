from django.core.management.base import BaseCommand, CommandError
import time,datetime
from performance.models import *
from performance.Queues import queues
from optparse import make_option

class Command(BaseCommand):
	help = "Run the specified performance test"
	option_list = BaseCommand.option_list + (
		make_option('--machine',
		action='store',
		dest='machine',
		default='localhost',
		help='Run performance test on machine'),
		make_option('--priority',
		action='store',
		dest='priority',
		type=int,
		default=5,
		help='Run performance test with priority'),
		make_option('--app',
		action='store',
		dest='application',
		help='Run performance test with the specified application'),
		make_option('--module',
		action='store',
		dest='module',
		help='Run performance test with the specified module'),
		make_option('--func',
		action='store',
		dest='function',
		help='Run performance test with the specified function'),
		make_option('--scenario',
		action='store',
		dest='scenario',
		help='Run performance test with the specified scenario'),
	)
		
	def handle(self,*args,**options):
		priority = 5
		machine = TestMachine.objects.get(hostname=options["machine"])
		if "machine" in options.keys():
			hostnames = options["machine"].split(",")
			machines = []
			for hostname in hostnames:
				machines.append(TestMachine.objects.get(hostname = hostname))
		if "prioirty" in options.keys():
			priority = options["priority"]
		app = Application.objects.get(app_name = options["application"])
		module = app.module_set.get(module_name = options["module"])
		function = module.function_set.get(func_name = options["function"])
		scenario = function.scenario_set.get(scenario_name = options["scenario"])
		ts = time.time()
		ts_f = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M")			

		
		testRun = TestRun(module=module,target=module.module_target,func_name=function.func_name.replace(" ","_"),ts_string=ts_f,result="Queued",priority=priority,machine=machine)
		testRun.save()
		queues.put(testRun.target, testRun)