from django.core.management.base import BaseCommand, CommandError
import time,datetime
from performance.models import *
from performance.Queues import queues
from optparse import make_option

class Command(BaseCommand):
	help = "Run all performance tests"
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
	)
		
	def handle(self,*args,**options):
		priority = 5
		machines = [TestMachine.objects.get(hostname="localhost")]
		if "machine" in options.keys():
			hostnames = options["machine"].split(",")
			machines = []
			for hostname in hostnames:
				machines.append(TestMachine.objects.get(hostname = hostname))
		if "prioirty" in options.keys():
			priority = options["priority"]

		ts = time.time()
		ts_f = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M")			

		
		for app in Application.objects.all():
			for module in app.module_set.all():
				for func in module.function_set.all():
					for machine in machines:
						testRun = TestRun(module=module,target=module.module_target,func_name=func.func_name.replace(" ","_"),ts_string=ts_f,result="Queued",priority=priority,machine=machine)
						testRun.save()
						queues.put(testRun.target, testRun)