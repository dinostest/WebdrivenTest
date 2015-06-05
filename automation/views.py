
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

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Max,Avg,Min,Sum
from automation.models import *
from multiprocessing import Process,Queue
from StringIO import StringIO
from django.contrib.auth.decorators import login_required
from django.db import connection
from config import robotCfg
import os, json, csv, urllib,re,random
import ConfigParser,shutil,subprocess,time,datetime
from robot.parsing.model import TestCaseFile



	
def index(request):
	apps = Application.objects.all()
	context = {'apps':apps, 'varList':robotCfg.ModuleVars + robotCfg.DataVars}
	return render(request, 'automation/index.html', context)
	
def loadapps(request):
	apps = Application.objects.all()
	results = []
	
	for app in apps:
		result = {}
		result['name'] = app.name
		result['modules'] = []
		for module in app.module_set.all():
			m = {}
			m['name'] = module.name
			m['functions'] = []
			for func in module.function_set.all():
				f = {}
				f['name'] = func.name
				f['scenarios'] = []
				for scenario in func.scenario_set.all():
					s = {}
					s['name'] = scenario.name;
					s['data_file'] = scenario.script;
					f['scenarios'].append(s)
				m['functions'].append(f)
			result['modules'].append(m)
		results.append(result)
	return HttpResponse(json.dumps(results), content_type="application/json")

def _set_status(item, status):
	if ('status' not in item.keys()):
		item['status'] = status
	elif (status == "running"):
		item['status'] = status
	elif (item['status'] != "running"):
		if (status == "Queued" ):
			item['status'] = status
		elif (item['status'] not in ["error","failed"] and status in ["error","failed"]):
			item['status'] = status
	
def loadall(request):
	apps = Application.objects.all()
	tag = None
	if ("priority" in request.GET.keys()):
		priority = int(request.GET["priority"])
	else:
		priority = 5
	if ("tag" in request.GET.keys()):
		tag_name = request.GET["tag"]
		tag = Tag.objects.get(tag_name = tag_name)
	
	if ("machine" in request.GET.keys()):
		machine_name = request.GET["machine"]
		machine = TestMachine.objects.get( label= machine_name)
	else:
		machine = TestMachine.objects.get( hostname= "localhost")
	
	res = {}
	results = []
	for app in apps:
		result = {}
		result['name'] = app.app_name
		result['modules'] = []
		for module in app.module_set.all():
			m = {}
			m['name'] = module.module_name
			m['funcs'] = []
#			path = os.path.join(robotCfg.TestPath,app.app_name, module.module_data);
#			cfg = ConfigParser.RawConfigParser()
#			cfg.optionxform = str
#			cfg.read(path)
#			functions = cfg.get("common","functions")
			for func in module.function_set.all():
				f = {}
				testRun = None
				f["name"] = func.func_name.replace(" ","_")
				testRuns = module.testrun_set.filter(func_name = f["name"], machine=machine).order_by("-timestamp")
				if (testRuns and len(testRuns) > 0):
					testRun = testRuns[0]
					f["status"] = testRun.result
				else:
					f["status"] = "initial"
				_set_status(m,f["status"])
				if (testRun):
					f["report"] = testRun.ts_string
					f["log"] = testRun.ts_string
				else:
					f["report"] = ""
					f["log"] = ""
				f["scenarios"] = []
				for scenario in func.scenario_set.all():
					s = {}
					s['name'] = scenario.scenario_name;
					s['data'] = scenario.scenario_data;
					if (testRun):
						s["status"] = testRun.result
						s["report"] = testRun.ts_string
						s["log"] = testRun.ts_string
					s["level"] = "scenario"
					s["priority"] = scenario.sample_set.aggregate(min_priority=Min('priority'))['min_priority']
					
					total = 0
					total_duration = 0
					failed = 0
					if (tag):
						samples = scenario.sample_set.filter(priority__lte = priority,is_deleted='N',tags__exact=tag.id)
					else:
						samples = scenario.sample_set.filter(priority__lte = priority,is_deleted='N')
					if testRun:
						for sample in samples:
							try:
								testReports = sample.testreport_set.filter(func_name=testRun.func_name,ts_string=testRun.ts_string,testrun = testRun)
							except TestReport.DoesNotExist:
								testReports=None
					
							if(testReports):
								_set_max(s,testReports.aggregate(max_duration=Max('response_time'))['max_duration'],'responsetime')
								total_duration = total_duration + int(testReports.aggregate(sum_duration=Sum('response_time'))['sum_duration'])
								total = total + testReports.count()
								failed = failed + testReports.filter(result='false').count()
						if (total > 0):
							s['avgtime'] = total_duration/total
							s['total'] = total
							s['failed'] = failed
							if (s['failed'] == 0):
								s['status'] = 'completed'					
							_set_max(f,s['responsetime'],'responsetime')
							_set_max(m,s['responsetime'],'responsetime')
							_set_max(result,s['responsetime'],'responsetime')
							_set_max(res,s['responsetime'],'responsetime')
						else:
							s['total'] = 0
							s['failed'] = 0
						_set_min(f,s['priority'],'priority')
						_set_min(m,s['priority'],'priority')
						_set_min(result,s['priority'],'priority')
						_set_min(res,s['priority'],'priority')
					f['scenarios'].append(s)
				
				_set_sum(f,'scenarios','total')
				_set_sum(f,'scenarios','failed')
				_set_avg(f,'scenarios','avgtime','total')
				m['funcs'].append(f)
			
			_set_sum(m,'funcs','total')
			_set_sum(m,'funcs','failed')
			_set_avg(m,'funcs','avgtime','total')
			_set_status(result,m["status"])
			result['modules'].append(m)
		_set_sum(result,'modules','total')
		_set_sum(result,'modules','failed')
		_set_avg(result,'modules','avgtime','total')
		_set_status(res,result['status'])
		results.append(result)
	res['data'] = results
	res['name'] = robotCfg.ProjectName
	_set_sum(res,'data','total')
	_set_sum(res,'data','failed')
	_set_avg(res,'data','avgtime','total')
	return HttpResponse(json.dumps(res), content_type="application/json")

def _set_sum(dict,listname,key):
	if listname in dict.keys():
		items = dict[listname]
		sum = 0
		for item in items:
			if key in item.keys():
				sum = sum + item[key]
			else:
				return
		dict[key] = sum
	
	
def _set_avg(dict,listname,key,num_key):
	if listname in dict.keys() and num_key in dict.keys():
		items = dict[listname]
		sum = 0
		for item in items:
			if key in item.keys():
				sum = sum + item[key] * item[num_key]
		if dict[num_key]:
			avg = int(sum/dict[num_key])
			dict[key] = avg
		else:
			return
	
def _set_max(dict, value, key):
	if key in  dict.keys():
		if value > dict[key]:
			dict[key] = value
	else:
		dict[key] = value

def _set_min(dict, value, key):
	if key in  dict.keys():
		if value < dict[key]:
			dict[key] = value
	else:
		dict[key] = value
		
def fetchscenario(request):
	id = int(request.GET["id"])
	s = Scenario.objects.get(id=id)
	rawdata = []	
	data = []
	for sample in s.sample_set.filter(is_deleted='N').order_by('line_no'):
		data_stream = StringIO(sample.value)
		reader = csv.reader(data_stream)
		for values in reader:
			item = dict(zip(s.sample_header.split(","),values))
			
		item['dinos_pkid'] = str(sample.id)
		item['Priority'] = str(sample.priority)
		tags = [tag.tag_name for tag in sample.tags.all()]
		item['Tag'] = ",".join(tags)
		data.append(item)
		
	
	result={}
	result["data"] = data
	headers = s.sample_header.split(",")
	headers.append('Priority')
	headers.append('Tag')
	settings = json.loads(s.settings)
	result["header"] = headers
	keywords = []
	for keyword in s.gherkins_keyword_set.filter(is_deleted = 'N'):
		item = {}
		keyword_name = keyword.name.encode('utf8','ignore')
		item["keyword"]=keyword_name
		item["dinos_pkid"]=keyword.id
		keywords.append(item)
	result["keywords"] = keywords
	result["settings"] = settings
	return HttpResponse(json.dumps(result), content_type="application/json")

	
def loaddata(request):
	app = request.GET["app"]
	func = request.GET["func"]
	module = request.GET["module"]
	scenario = request.GET["scenario"]
	a = Application.objects.get(name=app)
	m = a.module_set.get(name = module)
	func = func.replace("_"," ")
	f = m.function_set.get(name=func)
	s = f.scenario_set.get(name=scenario)
	rawdata = []
	data = []
	for sample in s.sample_set.filter(is_deleted='N').order_by('line_no'):
		data_stream = StringIO(sample.value)
		reader = csv.reader(data_stream)
		for values in reader:
			item = dict(zip(s.sample_header.split(","),values))
			
		item['dinos_pkid'] = str(sample.id)
		item['Priority'] = str(sample.priority)
		tags = [tag.tag_name for tag in sample.tags.all()]
		item['Tag'] = ",".join(tags)
		data.append(item)
		
	
	result={}
	result["data"] = data
	headers = s.sample_header.split(",")
	headers.append('Priority')
	headers.append('Tag')
	settings = json.loads(s.settings)
	result["header"] = headers
	keywords = []
	for keyword in s.gherkins_keyword_set.filter(is_deleted = 'N'):
		item = {}
		keyword_name = keyword.name.encode('utf8','ignore')
		item["keyword"]=keyword_name
		item["dinos_pkid"]=keyword.id
		keywords.append(item)
	result["keywords"] = keywords
	result["settings"] = settings
	return HttpResponse(json.dumps(result), content_type="application/json")

def _unique_sample_name(dict_list):
	dict_name={}
	for item in dict_list:
		sample_name = item['sample']
		if ( sample_name not in dict_name.keys()):
			dict_name[sample_name] = item
		elif (type(dict_name[sample_name]) == type({})):
			dict_name[sample_name]['sample'] = dict_name[sample_name]['sample'] + " 1" 
			item['sample'] = item['sample'] + " 2"
			dict_name[sample_name] = 3
		else:
			item['sample'] = item['sample'] + " " + str(dict_name[sample_name])
			dict_name[sample_name] = dict_name[sample_name] + 1

			
def _urlDecode(scenario, dict):
	for key in dict.keys():
		if (not key == 'sample'):
			if (dict[key]):
#				dict[key] = urllib.unquote_plus(dict[key])
				pass
			else:
				dict[key] = ""
	
	if 'sample' in  dict.keys():
		if dict['sample'].find(">>") <= 0:
			dict['sample'] = scenario.scenario_name + " >> " + dict['sample']
		else:
			dict['sample'] = scenario.scenario_name + " >> " + dict['sample'].split(">>")[1].strip()
#	if ('$Priority$' not in dict.keys()):
#		dict['$Priority$'] = 5
	
	return dict
	
def loadreport(app, datafile):
	path = os.path.join(robotCfg.TestPath,app,"report",datafile)
	csvFile = open(path,"r")
	data_list = []
	for line in csvFile.readlines():
		data = {}
		items = line.split(",")
		i = 0
		for header in robotCfg.JMeterHeader:
			data[header] = items[i]
			i = i+1
		if (data['Sample Name'].find(">>") > 0):
			try:
				sample = Sample.objects.get(sample_name = data['Sample Name'])
				data['Priority'] = sample.priority
			except Sample.DoesNotExist:
				data['Priority'] = "N/A"
		else:
			data['Priority'] = "N/A"
		if data['URL'] != 'null':
			data_list.append(data)
	
	result={}
	result["data"] = data_list
	result["header"] = robotCfg.ReportHeader
	return result

	
def loadscenario(request):
	app = request.GET["app"]
	module = request.GET["module"]
	func = request.GET["func"]
	scenario = request.GET["scenario"]
	application = Application.objects.get(name = app)
	m = application.module_set.get(name = module)
	f = m.function_set.get(name = func.replace("_"," "))
	s = f.scenario_set.get(name = scenario)
	settings = {}
	if s.sample_set.all().count() == 0:
		file_path = os.path.join(robotCfg.TestPath,app,s.script)
		testcase = TestCaseFile(source = file_path)
		testcase.populate()
		
		settings = robot_setting_dict(testcase.setting_table)
		if ('Documentation' in  settings.keys()):
			s.description = setting['Documentation']
		else:
			s.description = testcase.name
		if ('Resource' in settings.keys()):
			if (isinstance(settings['Resource'],list)):
				s.resource = ",".join(settings['Resource'])
			else:
				s.resource = settings['Resource']
		variables = robot_variable_dict(testcase.variable_table)
		s.settings = json.dumps(variables)
		s.sample_header = ",".join(testcase.testcase_table.header)
		s.save()
		for case in testcase.testcase_table:
			step = case.steps[0]
			data_stream = StringIO()
			csv_writer = csv.writer(data_stream)
			csv_writer.writerow([case.name] + case.steps[0].as_list())
			value = data_stream.getvalue().strip('\r\n')
			data_stream.close()
			sample = Sample(name=case.name,priority=5,value=value,is_deleted='N',scenario=s)
			sample.save()
		keywords = []
		for keyword in testcase.keywords:
			for step in keyword.steps:
				keyword_name = step.keyword.encode('utf8','ignore')
				k = Gherkins_keyword(name = keyword_name,args="\t".join(step.as_list()),scenario=s)
				keywords.append(keyword_name)
				k.save()
	else:
		settings = s.settings
		keywords = []
		for keyword in s.gherkins_keyword_set.all():
			keyword_name = keyword.name.encode('utf8','ignore').replace(" _"," {{").replace("_ ","}} ")
			if (keyword_name[-1] == "_"):
				keyword_name = keyword_name[:-1] + "}}"			
			keywords.append(keyword_name)
			
		columns = []
		for item in s.sample_header.encode('utf8','ignore').split(","):
			column = {}
			column["data"] = item
			column["title"] = item
			columns.append(column);
		
	is_popup = True
	context = {'app':app,'func':func,'scenario':scenario,'module':module, 'settings':settings,'keywords':keywords, 'tags': Tag.objects.all(),
		'columns':columns,'ng_app':'scenario'}
	return render(request, 'automation/scenario.html', context)
	
def robot_setting_dict(settings):
	dict = {}
	for setting in settings:
		values = setting.as_list()
		if len(values) > 1:
			if (values[0].encode('utf8','ignore') in dict.keys()):
				if isinstance(dict[values[0].encode('utf8','ignore')],list):
					dict[values[0].encode('utf8','ignore')].append(values[1].encode('utf8','ignore'))
				else:
					dict[values[0].encode('utf8','ignore')] = [dict[values[0].encode('utf8','ignore')],values[1].encode('utf8','ignore')]
			else:
				dict[values[0].encode('utf8','ignore')] = values[1].encode('utf8','ignore')
	return dict

def robot_variable_dict(settings):
	dict = {}
	for setting in settings:
		values = setting.as_list()
		if len(values) > 2:
			dict[values[0].encode('utf8','ignore')] = [x.encode('utf8','ignore') for x in values[1:]]
		elif len(values) == 2:
			dict[values[0].encode('utf8','ignore')] = values[1].encode('utf8','ignore')
	return dict
	
	
def loadplan(request):
	context = {}
	return render(request, 'performance/plan.html', context)
	
def loadplandata(request):
	plans = TestPlan.objects.all()
	data = []
	for plan in plans:
		item = []
		item.append(plan.name)
		item.append(plan.function.module.module_name)
		item.append(plan.function.func_name)		
		item.append(plan.start_threads)
		item.append(plan.end_threads)
		item.append(plan.increment)
		item.append(plan.loops)
		item.append(plan.wait_time)
		historical_runs = plan.testplanrun_set.all().order_by("-ts_string")
		if historical_runs.count() > 0:
			lastrun = historical_runs[0]
			item.append(lastrun.status)
		else:
			item.append("inital")
		data.append(item)
	return HttpResponse(json.dumps(data), content_type="application/json")
		
def loadplanrun(request):
	plan_name = request.GET["testplan"]
	testplan = TestPlan.objects.get(name=plan_name)
	testplanruns = testplan.testplanrun_set.all().order_by("-ts_string")
	if len(testplanruns) > 0:
		status = testplanruns[0].status
		if status == "running":
			result = loadruns(testplanruns[0])
			return HttpResponse(json.dumps(result), content_type="application/json")
			
	header = ["Start Time","Plan Name", "Module Name", "Function Name", "Start Threads","End Threads","Increment", "Loops","Wait Time","Status"]
	data = []
	for run in testplanruns:
		item = []
		item.append(run.ts_string)
		item.append(run.name)
		item.append(run.testplan.function.module.module_name)
		item.append(run.testplan.function.func_name)		
		item.append(run.start_threads)
		item.append(run.end_threads)
		item.append(run.increment)
		item.append(run.loops)
		item.append(run.wait_time)
		item.append(run.status)
		data.append(item)
	result={}
	result["header"] = header
	result["data"] = data
	if len(testplanruns) > 0:
		result["status"] = testplanruns[0].status
	return HttpResponse(json.dumps(result), content_type="application/json")
			

def runplan(request):
	data = json.loads(request.body)
	testplan = TestPlan.objects.get(name = data["Plan Name"])
	testplan.start_threads = int(data["Start Threads"])
	testplan.end_threads = int(data["End Threads"])
	testplan.increment = int(data["Increment"])
	testplan.loops = int(data["Loops"])
	testplan.wait_time = int(data["Wait Time"])
	testplan.save()
	now_time = datetime.datetime.now()
	times = int(data["times"])
	for num in range(times):
		ts_string = now_time.strftime("%Y-%m-%d_%H-%M")
		print ts_string
		testplanrun = TestPlanRun(name=testplan.name,description=testplan.description,start_threads=testplan.start_threads,end_threads=testplan.end_threads,wait_time=testplan.wait_time,increment=testplan.increment,loops=testplan.loops,status="running",testplan=testplan,ts_string=ts_string)
		testplanrun.save()
		threads = testplanrun.start_threads
		count = 0
		machine = TestMachine.objects.get(hostname="localhost")
		while (threads <= testplanrun.end_threads):
			testrun = TestRun(func_name = testplan.function.func_name.replace(" ","_"),ts_string=ts_string + "." + str(count),target=testplan.function.module.module_target,result="Queued",loops=testplan.loops,wait_time=testplan.wait_time,threads = threads,module=testplan.function.module,testplanrun=testplanrun,priority=5,machine=machine)
			testrun.save()
			threads = threads + testplan.increment
			count = count + 1
			queues.put(testrun.target, testrun)
		now_time = now_time + datetime.timedelta(minutes=1)
	result = loadruns(testplanrun)

	return HttpResponse(json.dumps(result), content_type="application/json")

def loadruns(testplanrun):
	testruns = testplanrun.testrun_set.all()
	header = ["Start Time","Threads","Wait Time","Loops","Satus"]
	data = []
	for testrun in testruns:
		item = []
		if not (testrun.result == "running" or testrun.result == "Queued"):
			item.append("<a target='_blank' href='/performance/report/" + testrun.func_name +"?ts=" + testrun.ts_string + "&machine=" + urllib.quote_plus(testrun.machine.label) + "'>" + testrun.ts_string + "</a>")
		else:
			item.append(testrun.ts_string)
		item.append(testrun.threads)
		item.append(testrun.wait_time)
		item.append(testrun.loops)
		item.append(testrun.result)
		data.append(item)
	result = {}
	result["header"] = header
	result["data"] = data
	result["status"] = testplanrun.status
	return result
	
def planresult(request):
	plan_name = request.GET["planname"]
	
	testplan = TestPlan.objects.get(name = plan_name)
	func_name = testplan.function.func_name
	if ("ts" in request.GET.keys()):
		ts_string = request.GET["ts"]
		testplanruns = [testplan.testplanrun_set.get(ts_string = ts_string)]
	if ("lastrun" in request.GET.keys()):
		lastrun = int(request.GET["lastrun"])
		testplanruns = [testplanrun for testplanrun in testplan.testplanrun_set.exclude(ts_string__isnull = True).order_by("-ts_string")][:lastrun]
		
	
	labels = []
	testrun_results=[]
	failratio = {}
	failratio["id"] = "fail_ratio"
	failratio["name"] = "Failure Ratios"
	failratio["group"] = []
	
	
	avg_response_time = {}
	avg_response_time["id"] = "avg_response_time"
	avg_response_time["group"] = []
	
	avg_response_time["name"] = "Average Response Time"
	results = [failratio,avg_response_time]
	headers = ['Start Time','Threads','Loops','Wait Time','Function','Fail Ratio','Average Response Time']
	data = []
	alltestruns = TestRun.objects.filter(testplanrun__in = testplanruns)
	testplan_runs={}
	for testrun in alltestruns:
		if testrun.testplanrun_id not in testplan_runs.keys():
			testplan_runs[testrun.testplanrun_id] = [testrun]
		else:
			testplan_runs[testrun.testplanrun_id].append(testrun)
		
	for testplanrun in testplanruns:
	
		testRuns = testplan_runs[testplanrun.id]
		fail_group = {}
		fail_group["data"] = []
		
		fail_group["ts_string"] = testplanrun.ts_string
		avg_group = {}
		avg_group["ts_string"] = testplanrun.ts_string
		avg_group["data"] = []
		
		
		for item in [fail_group,avg_group]:
			item["red"] = int(random.random() * 255)
			item["green"] = int(random.random() * 255)
			item["blue"] = int(random.random() * 255)
			if item["red"] + item["green"] + item["blue"] > 600:
				item["red"] = 255 - item["red"]
				item["green"] = 255 - item["green"]
				item["blue"] = 255 - item["blue"]
				
		failitem = {}
		avgitem = {}
		for testrun in testRuns:
			line = []
			if not (testrun.result == "running" or testrun.result == "Queued"):
				if (testrun.threads not in labels):
					labels.append(testrun.threads)
				line.append("<a target='_blank' style='color:blue' href='/performance/report/" + testrun.func_name +"?ts=" + testrun.ts_string + "&machine=" + urllib.quote_plus(testrun.machine.label) + "'>" + testplanrun.ts_string + "</a>")
				line.append(testrun.threads)
				line.append(testrun.loops)
				line.append(testrun.wait_time)
				
				line.append(func_name)
				
				if (not testrun.fail_ratio == None):
					fail_ratio = testrun.fail_ratio
				else:
					fail_ratio= testrun.testreport_set.filter(result="false").count()* 100/testrun.testreport_set.all().count()
					testrun.fail_ratio = fail_ratio
					testrun.save()
					
				failitem[testrun.threads] = fail_ratio
				
				line.append(fail_ratio)
				
				if (testrun.avg_response_time):
					avgtime = testrun.avg_response_time
				else:
					avgtime = int(testrun.testreport_set.all().aggregate(Avg('response_time'))["response_time__avg"])
					testrun.avg_response_time = avgtime
					testrun.save()
				
				avgitem[testrun.threads] = avgtime
				
				line.append(avgtime)
				data.append(line)
		for key in labels:
			if key in failitem.keys():
				fail_group["data"].append(failitem[key])
				avg_group["data"].append(avgitem[key])
			else:
				fail_group["data"].append(None)
				avg_group["data"].append(None)
				
		avg_response_time["group"].append(avg_group)
		failratio["group"].append(fail_group)
	context={'labels':labels,'data':data,'results':results,'headers':headers}
	return render(request, 'performance/planresult.html', context)
	
def loadcfg(request):
	app = request.GET["app"]
	module = request.GET["module"]
	a_module = Module.objects.get(name=module);
	if ("func" in request.GET.keys()):
		func_name = request.GET["func"].replace("_"," ");
		function = a_module.function_set.get(name = func_name)
	else:
		function = a_module.function_set.all()[0]
	# path = os.path.join(robotCfg.TestPath,app, a_module.module_data);
	# cfg = ConfigParser.RawConfigParser()
	# cfg.optionxform = str
	# cfg.read(path)
	data = {}
	setting = json.loads(function.settings)
	for (key,value) in setting.items():
		data[key] = value
	funcs = [func.name for func in a_module.function_set.all()]
	data["functions"] = ",".join(funcs)
	# for (key,value) in  cfg.items("common"):
		# data[key] = value
	m_info = {}
	
	result = {}
	result["func"] = function.name
	result["scenarios"] = []
	for scenario in function.scenario_set.all():
		s = {}
		s["name"] = scenario.name
		s["description"] = scenario.description
		s["data"] = scenario.script
		result["scenarios"].append(s)
	result["app"] = app
	result["data"] = data
	result["name"] = module
	result["module"] = m_info
	return HttpResponse(json.dumps(result), content_type="application/json")

def savescenario(request):
	id = int(request.GET["id"])
	scenario = Scenario.objects.get(id = id)
	scenario.gherkins_keyword_set.all().update(is_deleted = 'Y')
	scenario.sample_set.all().update(is_deleted = 'Y')
	app = scenario.func.module.application.name
	path = os.path.join(robotCfg.TestPath,app,scenario.script)
	backup_path = path + ".bak"
	if (os.path.exists(path)):
		shutil.copy(path, backup_path)
	data = json.loads(request.body)
	header = data["header"][:-3]
	sampleData = data["data"]
	settings = data["setting"]
	keywords = data["keywords"]
	scenario.description = data["description"]
	scenario.name = data["name"]
	scenario.resource=data["resource"]
	scenario.settings = json.dumps(settings)
	scenario.save()
	
	robot_file = open(path,"w")
	robot_file.write("*** Settings ***\n")
	robot_file.write("Documentation\t" + scenario.description +"\n")
	for resource in scenario.resource.split(","):
		robot_file.write("Resource\t" + scenario.resource +"\n")
	robot_file.write("Test Template\t" + scenario.name +"\n")
	robot_file.write("\n")
	keys = settings.keys()
	if len(keys) > 0:
		robot_file.write("*** Variables ***\n")
	
	for key in settings.keys():
		robot_file.write(key + "\t" +settings[key] +"\n")
	robot_file.write("\n")
	
	robot_file.write("*** Test Cases ***\t" + "\t".join(header[1:]) + "\n");
	line_no = 0
	for item in sampleData:
		if (item["Test Cases"]):
			if (not item["Priority"]):
				priority = 5
			else:
				priority = int(item["Priority"])
			data_stream = StringIO()
			csv_writer = csv.DictWriter(data_stream,header)
			new_item = {}
			for key in header:
				new_item[key] = item[key]
			csv_writer.writerow(new_item)
			value = data_stream.getvalue().strip('\r\n')
			data_stream.close()
			if ("dinos_pkid" in item.keys() and item["dinos_pkid"]):
				sample=Sample.objects.get(id=int(item["dinos_pkid"]))
				sample.name = item["Test Cases"]				
				sample.priority = priority
				sample.line_no = line_no
				sample.value = value
				sample.is_deleted='N'

			else:				
				sample = Sample(name = item["Test Cases"],scenario=scenario,priority= priority,value=value,line_no = line_no, is_deleted='N')
			sample.save()
			
			if (item["Tag"]):
				tagsValue = item["Tag"]
			else:
				tagsValue = ""
			tags = tagsValue.split(",")
			original_tags= [tag.tag_name for tag in sample.tags.all()]
			for tag in tags:
				if len(tag) > 0 and tag not in original_tags:
					sample.tags.add(Tag.objects.get(tag_name=tag))
				for tag in original_tags:
					if tag not in tags:
						sample.tags.remove(Tag.objects.get(tag_name=tag))
			
			
				
			for key in header:
				if (item[key]):
					robot_file.write(item[key] + "\t")
				else:
					robot_file.write(" "+"\t")
			robot_file.write("\n")
			line_no = line_no + 1
	robot_file.write("\n")
	robot_file.write("*** Keywords ***\n")
	robot_file.write(scenario.name + "\t[Arguments]")
	for argument in header[1:]:
		robot_file.write("\t${" + argument + "}")
	robot_file.write("\n")
	line_no = 0
	for keyword in keywords:
		robot_file.write("\t" + keyword["keyword"])
		if ("dinos_pkid" in keyword.keys() and keyword["dinos_pkid"]):
			gkeyword = Gherkins_keyword.objects.get(id = int(keyword["dinos_pkid"]))
			gkeyword.name = keyword["keyword"]
			gkeyword.scenario = scenario
			gkeyword.line_no = line_no
			gkeyword.is_deleted = 'N'
		else:
			gkeyword = Gherkins_keyword(name=keyword["keyword"],args=keyword["keyword"],scenario = scenario,line_no = line_no)
		gkeyword.save()
		items = keyword["keyword"].split("\"")
		for i in range(len(items)/2):
			if 2*i + 1 < len(items):
				robot_file.write("\t${" + items[2*i + 1] + "}")
		robot_file.write("\n")
		line_no = line_no + 1
			
	result = "OK"
	return HttpResponse(json.dumps(result), content_type="application/json")
	
def savenode(request):
	type = request.GET["type"]
	data = json.loads(request.body)
	if (type == "Project"):
		robotCfg.description = data["description"]
		Application.objects.all().update(is_deleted = 'Y')
		for app in data["children"]:
			if app["id"]:
				app_id = int(app["id"])
				application = Application.objects.get(id = app_id)
				application.name = app["name"]
				application.description = app["description"]
			else:
				application = Application(name = app["name"],description=app["description"])
			application.is_deleted = 'N'
			application.save()
	else:
		id = int(request.GET["id"])
		
		if (type == "Application"):
			ItemClass = Application
			parent = "application"
			ChildClass = Module
		if (type == "Module"):
			ItemClass = Module
			parent = "module"
			ChildClass = Function
		if (type == "Function"):
			ItemClass = Function
			parent = "func"
			ChildClass = Scenario
		ChildClass.objects.all().update(is_deleted = 'Y')
		node = ItemClass.objects.get(id = id)
		node.name = data["name"]
		node.description = data["description"]
		node.save()
		for item in data["children"]:
			if item["id"]:
				item_id = int(item["id"])
				child = ChildClass.objects.get(id = item_id)
				child.name = item["name"]
				child.description = item["description"]
			else:
				child = ChildClass(name=item["name"],description=item["description"])
				setattr(child,parent,node)
				if (type == "Function"):
					child.settings = "{}"
					child.sample_header = "Test Cases"
					child.script=child.name.replace(" ","_") + ".txt"
			child.is_deleted = 'N'
			child.save()
			item["id"] = child.id
	return HttpResponse(json.dumps(data), content_type="application/json")		

def savedata(request):
	app = request.GET["app"]
	func = request.GET["func"]
	module = request.GET["module"]
	s_name = request.GET["scenario"]
	a = Application.objects.get(name=app)
	m = a.module_set.get(name = module)
	func = func.replace("_"," ")
	f = m.function_set.get(name=func)
	scenario = f.scenario_set.get(name=s_name) 
	scenario.gherkins_keyword_set.all().update(is_deleted = 'Y')
	scenario.sample_set.all().update(is_deleted = 'Y')
	path = os.path.join(robotCfg.TestPath,app,scenario.script)
	backup_path = path + ".bak"
	if (os.path.exists(path)):
		shutil.copy(path, backup_path)
	data = json.loads(request.body)
	header = data["header"][:-2]
	sampleData = data["data"]
	settings = data["setting"]
	keywords = data["keywords"]
	
	robot_file = open(path,"w")
	robot_file.write("*** Settings ***\n")
	for key in settings.keys():
		robot_file.write(key + "\t" +settings[key] +"\n")
	robot_file.write("\n")
	
	robot_file.write("*** Test Cases ***\t" + "\t".join(header[1:]) + "\n");
	line_no = 0
	for item in sampleData:
		if (item["Test Cases"]):
			data_stream = StringIO()
			csv_writer = csv.DictWriter(data_stream,header)
			new_item = {}
			for key in header:
				new_item[key] = item[key]
			csv_writer.writerow(new_item)
			value = data_stream.getvalue().strip('\r\n')
			data_stream.close()
			if ("dinos_pkid" in item.keys() and item["dinos_pkid"]):
				sample=Sample.objects.get(id=int(item["dinos_pkid"]))
				sample.name = item["Test Cases"]				
				sample.priority = int(item["Priority"])
				sample.line_no = line_no
				sample.sample_value = value
				sample.is_deleted='N'

			else:
				sample = Sample(name = item["Test Cases"],scenario=scenario,priority= int(item["Priority"]),sample_value=value,line_no = line_no, is_deleted='N')

			tagsValue = item["Tag"]
			tags = tagsValue.split(",")
			original_tags= [tag.tag_name for tag in sample.tags.all()]
			for tag in tags:
				if len(tag) > 0 and tag not in original_tags:
					sample.tags.add(Tag.objects.get(tag_name=tag))
				for tag in original_tags:
					if tag not in tags:
						sample.tags.remove(Tag.objects.get(tag_name=tag))
			
			sample.save()
				
			for key in header:
				robot_file.write(item[key] + "\t")
			robot_file.write("\n")
			line_no = line_no + 1
	robot_file.write("\n")
	robot_file.write("*** Keywords ***\n")
	robot_file.write(settings["Test Template"] + "\t[Arguments]")
	for argument in header[1:]:
		robot_file.write("\t${" + argument + "}")
	robot_file.write("\n")
	line_no = 0
	for keyword in keywords:
		robot_file.write("\t" + keyword["keyword"])
		if ("dinos_pkid" in keyword.keys() and keyword["dinos_pkid"]):
			gkeyword = Gherkins_keyword.objects.get(id = int(keyword["dinos_pkid"]))
			gkeyword.name = keyword["keyword"]
			gkeyword.scenario = scenario
			gkeyword.line_no = line_no
			gkeyword.is_deleted = 'N'
		else:
			gkeyword = Gherkins_keyword(name=keyword["keyword"],args=keyword["keyword"],scenario = scenario,line_no = line_no)
		gkeyword.save()
		items = keyword["keyword"].split("\"")
		for i in range(len(items)/2):
			if 2*i + 1 < len(items):
				robot_file.write("\t${" + items[2*i + 1] + "}")
		robot_file.write("\n")
		line_no = line_no + 1
		
	# minRemove_line = len(sheetdata)
	# for pkid in dbChanges["removeList"]:
		# sample = Sample.objects.get(id=int(pkid))
		# if minRemove_line > sample.line_no:
			# minRemove_line = sample.line_no
		# sample.is_deleted = 'Y'
		# sample.save()
#	scenario.sample_set.filter(is_deleted='N').update(is_deleted='Y')
	# line_no = 1
	# insert_lines = 0
	# for line in sheetdata:

		# if line and line[0]:		
#			sample,created = scenario.sample_set.get_or_create(sample_name = line[0],defaults={'scenario':scenario,'priority':5,'is_deleted':'N'})
#			sample.priority = int(line[-1])
#			sample.is_deleted = 'N'
#			sample.save()
#			sample.fields_set.filter(is_deleted='N').update(is_deleted='Y')
#			for item in header[1:-1]:
#				field,created = sample.fields_set.get_or_create(field_name = item,field_value=line[header.index(item)],defaults={'field_type':"String",'sample':sample,'is_deleted':'N'})
#				if (not created):
#					field.is_deleted = 'N'
#				field.save()
			# data_line = map(lambda x: "" if (x == None) else x, line)
			# #data_line = map(lambda x: "" if (x == None) else urllib.quote_plus(str(x)), line[1:len(header)])
			# data_stream = StringIO()
			# csv_writer = csv.DictWriter(data_stream,header)
			# item = dict(zip(header,data_line))
			# csv_writer.writerow(item)
			# value = data_stream.getvalue().strip('\r\n')
			# data_stream.close()
			# if (len(line) > len(header)):
				# dinos_pkid = line[-1]
				# priority = line[-2]
				# if (not priority):
					# priority = 5
				# else:
					# priority = int(priority)
					
				# if (not dinos_pkid):
					# sample = Sample(sample_name = line[0],scenario=scenario,priority= priority,sample_value=value,line_no = line_no, is_deleted='N')
					# insert_lines = insert_lines + 1
					# sample.save()				
				# elif (dinos_pkid in dbChanges["changeList"] or insert_lines > 0 or line_no > minRemove_line):
					# sample=Sample.objects.get(id=int(dinos_pkid))
					# sample.sample_name = line[0]
					# sample.priority = int(line[-3])
					# tagsValue = line[-2].strip()
					# tags = tagsValue.split(",")
					# original_tags= [tag.tag_name for tag in sample.tags.all()]
					# for tag in tags:
						# if len(tag) > 0 and tag not in original_tags:
							# sample.tags.add(Tag.objects.get(tag_name=tag))
					# for tag in original_tags:
						# if tag not in tags:
							# sample.tags.remove(Tag.objects.get(tag_name=tag))
					# sample.line_no = line_no
					# sample.sample_value = value
					# sample.is_deleted='N'
					# sample.save()
			# else:
				# sample = Sample(sample_name = line[0],scenario=scenario,priority=int(line[-2]),sample_value=value,line_no = line_no, is_deleted='N')
				# sample.save()
			# line_no = line_no + 1	
			# csv_file.write( value + "\n")
	
	result = "OK"
	return HttpResponse(json.dumps(result), content_type="application/json")
	
	
def savecfg(request):
	app = request.GET["app"]
	name = request.GET["module"]
	module = Module.objects.get(module_name=name)
	func = request.GET["func"]
	func_name = func.replace("_"," ")
	function = module.function_set.get(func_name=func_name)
	data = json.loads(request.body)
	module.module_threads = data["module"]["threads number"]
	module.module_target = data["module"]["Server to be tested"]
	module.module_loop = data["module"]["loop number"]
	module.module_ramp_up = data["module"]["ramp up seconds"]
	module.save()
	
#	cfg = ConfigParser.RawConfigParser()
#	cfg.optionxform = str
#	path = os.path.join(robotCfg.TestPath,app,module.module_data)
	# if (os.path.exists(path)):
		# backup_path = path + ".bak"
		# shutil.copy(path, backup_path)
		# cfg.read(path)
		
	setting = {}
	for item in data["cfg"]:
#		cfg.set("common",item["Key"],item["Value"])
		setting[item["Key"]] = item["Value"]
	function.func_setting = json.dumps(setting);
	function.save()
	# cfg_file = open(path, "w");
	# cfg.write(cfg_file)
	# cfg_file.close()
	result={}
	result["module"]=module.module_name
	result["func"] = func
	result["filelist"] = "filelist" in setting.keys()
	result["thread-datalist"] = "thread-datalist" in setting.keys()
	return HttpResponse(json.dumps(result), content_type="application/json")

def loadstatus(request,module,func):
	result={}
	result["func"] = func
	result["module"] = module
	path = os.path.join(robotCfg.TestPath,"lock",".".join([module,func,"lock"]))
	if "ts_f" in request.GET.keys():
		ts_f = request.GET["ts_f"]
		testRun = TestRun.objects.get(func_name=func, ts_string=ts_f)
		result["status"] = testRun.result
		result["ts_f"] = ts_f
	else:
		testRuns = TestRun.objects.filter(func_name=func).order_by('-timestamp')
		if testRuns and len(testRuns) > 0:
			testRun = testRuns[0]
			result["ts_f"] = testRun.ts_string
			result["status"] = testRun.result
		else:
			result["status"] = "initial"
			
	if (os.path.isfile(path)):
		result["status"] = "running"
	
	if not result["status"] or len(result["status"]) == 0:
		result["status"] = "unknown"

	return HttpResponse(json.dumps(result), content_type="application/json")

def report(request, func):
	ts = request.GET["ts"]
	items = ts.split("_")
	scenario = "" 
	
	priority = None
	machine = TestMachine.objects.get(hostname="localhost")
	if ("priority" in request.GET.keys()):
		priority = int(request.GET["priority"])
	else:
		priority = 5

	if ("machine" in request.GET.keys()):
		machine = TestMachine.objects.get(label=request.GET["machine"].replace("_", " "))
		
	timestamp = items[0] + " " + items[1].replace("-",":")
	
	#try:
	testRun = TestRun.objects.get(func_name = func, ts_string = ts,machine=machine)
	testReports = TestReport.objects.filter(func_name = func, ts_string = ts,testrun = testRun)
	target = testRun.target
	module = testRun.module
	if ("scenario" in request.GET.keys()):
		scenario = urllib.unquote_plus(request.GET["scenario"])
	
	reports = []
	for testReport in testReports:
		reports.append(testReport.JMeterDict())
	app = module.application
	report_file = ".".join([module.module_name,func,ts,"csv"])
#	report_path = os.path.join(robotCfg.TestPath, app.app_name,"report", report_file)
#	result = loadreport(app.app_name, report_file)
	data = []
	for line in reports:
		data_line = []
		for item in robotCfg.ReportHeader:
			data_line.append(line[item])
			
		if (data_line[0].find(scenario) >= 0 ):
			if (priority and type(line['Priority']) == type(1)):
				if (line['Priority'] <= priority):
					data.append(data_line)
			else:	
				data.append(data_line)

	context = { 'is_popup': True, 'reportFile': report_file, 'app': app.app_name, 
		'report_name': 'Performance test report for ' + func,'time_stamp':timestamp,'target':target,
		'data':data,
		'machine': machine.label,
		'header': robotCfg.ReportHeader
		}
	return render(request, 'performance/report.html', context)
	#except Exception as e:
	#	context = { 'is_popup': True, 'errMsg': str(e)}
	#	return render(request, 'performance/error.html', context)
		
def log(request, func):
	ts = request.GET["ts"]
	machine = request.GET["machine"]
	testRun = TestRun.objects.get(func_name = func, ts_string = ts,machine=TestMachine.objects.get(label = machine))
	remote_server = testRun.machine.hostname
	module = testRun.module
	app = module.application
	log_file = ".".join([module.module_name,func,ts,remote_server,"log"])
	log_path = os.path.join(robotCfg.TestPath, app.app_name,"log", log_file)
	try:
		f = open(log_path, "r")
		messages = f.readlines()
		f.close()
		context = { 'is_popup': True, 'logFile': log_file, 'app': app.app_name, 'log_name': 'Jmeter log for ' + func, 'msgs': messages }
		return render(request, 'performance/log.html', context)

	except Exception as e:
		context = { 'is_popup': True, 'errMsg': str(e)}
		return render(request, 'performance/error.html', context)
		
	
def runtest(request):
	data = json.loads(request.body)
	module = data["module"]
	func = data["func"]
	scenario = data["scenario"]
	machine = TestMachine.objects.get(hostname="localhost")
	priority = 5
	if ("priority" in data.keys()):
		priority = int(data["priority"])
	 
	ts = time.time()
	ts_f = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M")
	m = Module.objects.get(module_name=module)
	func_name = func.replace("_", " ")
	function = m.function_set.get(func_name = func_name)
	appname = m.application.app_name
	s = function.scenario_set.get(name=scenario)
	testRun = TestRun(scenario=s,target=s.target,name=ts_f,ts_string=ts_f,result="Queued", machine = machine,priority=priority)
	testRun.save()
	print connection.queries
	#t_runtest(module,func,ts_f);
	if "run_in_parallel" in data.keys():
		p = Process(target=runTest, args=(testRun,))
		p.start()
	else:
		queues.put(testRun.target, testRun)
		
		
	#p.join()
	result={}
	result["module"] = data["module"]
	result["func"]= data["func"]
	result["ts_f"]=ts_f
	return HttpResponse(json.dumps(result), content_type="application/json")

	
def runTest(testRun):
	scenario = testRun.scenario
	name = scenario.name
	func = scenario.function.name
	ts_f = testRun.ts_string
	_createLock(name,func)
	try:
		testRun.result = "running"
		testRun.save()
		app = module.application
		testlog_path = os.path.join(robotCfg.TestPath, app.app_name,"log", ".".join([name,func,ts_f,"log"]))
		testreport_path = os.path.join(robotCfg.TestPath, app.app_name,"report", ".".join([name,func,ts_f,"csv"]))
#		testcfg_path = os.path.join(robotCfg.TestPath, app.app_name, module.module_data)
		func_name = func.replace("_", " ")
#		function = module.function_set.get(func_name = func_name);
		settings = json.loads(scenario.settings)
		scriptpath = os.path.join(robotCfg.TestPath,app.app_name,scenario.script)
		robot_file = open(scriptpath,"w")

		robot_file.write("*** Settings ***\n")
		for key in settings.keys():
			robot_file.write(key + "\t" +settings[key] +"\n")
		robot_file.write("\n")
		
		header = scenario.header.split(",")
		robot_file.write("*** Test Cases ***\t" + "\t".join(header[1:]) + "\n");
		
		samples = scenario.sample_set.filter(is_deleted="N",priority__lte=testRun.priority).order_by("line_no")
		for sample in samples:
			csv_file.write(("\t").join(sample.sample_value.split(",")) + "\n")
		csv_file.close()

		
		# cfg = ConfigParser.RawConfigParser()
		# cfg.optionxform = str
		# cfg.read(testcfg_path)
		arg_list = [robotCfg.RobotPath,  "-l" + testlog_path, "-r" + testreport_path, scriptpath]
		# for (key,value) in cfg.items("common"):
			# if key != "functions":
				# arg_list.append("-J" + key + "=" +value)
		# if cfg.has_section(func_name):
			# for (key,value) in cfg.items(func_name):
				# arg_list.append("-J" + key + "=" +value)
		
		for (key,value) in setting.items():
			arg_list.append("-J" + key + "=" +value)
		
			
		result = subprocess.call(arg_list)
		if  result == 0:		
			testRun.result = _checkLog(testlog_path)
		else:
			testRun.result = "error"
		populate_report(module,testRun,testreport_path)
		testRun.save()
		
		total_tests = testRun.testreport_set.all().count()
		if (total_tests > 0):
			testRun.fail_ratio = testRun.testreport_set.filter(result = 'false').count() * 100/total_tests
			testRun.avg_response_time = testRun.testreport_set.all().aggregate(Avg('response_time'))['response_time__avg']
			testRun.save()
			
			
		if (testRun.testplanrun):
			testplanrun = testRun.testplanrun
			testruns = testplanrun.testrun_set.all()
			is_completed = True
			for testrun in testruns:
				if testrun.result == "running" or testrun.result == "Queued":
					is_completed = False
					break
			if is_completed:
				testplanrun.status = "completed"
				testplanrun.save()
		
			
		_removeLock(name,func)
		if (testRun.wait_time):
			time.sleep(testRun.wait_time)
	
	except Exception as e:
		testRun.result = "exception"
		testRun.message = str(e)
		testRun.save()
		_removeLock(name,func)
		
	return testRun.result

def populate_report(module,testRun, report_path):

	csvFile = open(report_path,"r")
	reader = csv.DictReader(csvFile, fieldnames = robotCfg.JMeterHeader)
	
	for data in reader:
		if (data['Result'] == 'false' and testRun.result == 'completed'):
			testRun.result = 'failed'
			testRun.save()
			
		if (data['Sample Name'].find(">>") > 0):
			sampleName = data['Sample Name']
			scenario_name,sample_name = data['Sample Name'].split(">>")
			func_name = testRun.func_name.replace("_", " ")
			function = module.function_set.get(func_name = func_name)
			scenario_name = scenario_name.strip()
			scenario = function.scenario_set.get(scenario_name=scenario_name)
			sample_name = sampleName.strip()
			time_stamp = data['Time Stamp']
#			if time_stamp.find(".") > 0:
#				time_stamp = time_stamp[:time_stamp.find(".")]
#			running_time = datetime.datetime.strptime(time_stamp,"%Y-%m-%d %H:%M:%S")
			isCreated = False
			for sample in scenario.sample_set.filter(is_deleted='N'):
				if sampleName.find(sample.sample_name) >= 0:
					testReport = TestReport(func_name=testRun.func_name,sample_name=sample_name,response_time=data['Response Time'],URL=data['URL'],timestamp=time_stamp,response_code = data['Response Code'],ts_string=testRun.ts_string,target=testRun.target,result=data['Result'],message=data['Response Message'],sample=sample,type=data['Type'],thread_name=data['Thread Name'],latency=data['Latency'],bytes=data['Bytes'],testrun=testRun)
					testReport.save()
					isCreated = True
					break
			if not isCreated:
				sample = scenario.sample_set.get(sample_name="others")
				testReport = TestReport(func_name=testRun.func_name,sample_name=sample_name,response_time=data['Response Time'],URL=data['URL'],timestamp=time_stamp,response_code = data['Response Code'],ts_string=testRun.ts_string,target=testRun.target,result=data['Result'],message=data['Response Message'],sample=sample,type=data['Type'],thread_name=data['Thread Name'],latency=data['Latency'],bytes=data['Bytes'],testrun=testRun)
				testReport.save()
				
			
			
	
	
def _checkLog(log_file):
	logfile = open(log_file, "r")
	data = logfile.readlines()
	logfile.close()
	failed  = filter(lambda x: "failed" in x,data)
	error =  filter(lambda x:"ERROR" in x,data)
	if len(failed) > 0:
		return "failed"
	elif len(error) > 0:
		return "error"
	else:
		return "completed"

def _createLock(name,func):
	path = os.path.join(robotCfg.TestPath,"lock",".".join([name,func,"lock"]))
	if (os.path.isfile(path)):
		raise Exception("Only allow one instance running for one function")
	file = open(path,"w")
	file.write(str(os.getpid()))
	file.close()

def _removeLock(name,func):
	path = os.path.join(robotCfg.TestPath,"lock",".".join([name,func,"lock"]))
	if (os.path.isfile(path)):
		os.remove(path)

def _add_item(all_items,name,level,prefix):
	a_item = {}
	a_item["name"] = name
	a_item["level"] = level
	a_item["prefix"] = prefix
	all_items.append(a_item)

@login_required(login_url='/admin/login.html')
def dashboard(request):
	apps= Application.objects.all()
	all_items = []
	for app in apps:
		modules = app.module_set.all()
		aName = app.app_name
		_add_item(all_items,aName,1,aName)
		
		for module in modules:
			mName = module.module_name
			_add_item(all_items,mName,2,aName + "-" + mName)
			# path = os.path.join(robotCfg.TestPath,aName,module.module_data)
			# cfg = ConfigParser.RawConfigParser()
			# cfg.optionxform = str
			# cfg.read(path)
			#functions = cfg.get("common","functions").split(",")
			
			for function in module.function_set.all():
				idName = aName + "-" + mName + "-" + function.func_name.replace(" ","_")
				name = function.func_name
				_add_item(all_items,name,3,idName )
				scenarios = function.scenario_set.all()
				for scenario in scenarios:
					name = scenario.scenario_name
					sIDName = idName + "-" + name.replace(" ","_")
					_add_item(all_items,name,4,sIDName)

	context = {'all_items':all_items, 'tags': Tag.objects.all(),'title' : "Performance Test Dashboard",'machines' : TestMachine.objects.all()}
	return render(request, 'performance/dashboard.html', context)
					
def loadfiletable(request):
	name = request.GET["module"]
	func_name = request.GET["func_name"] 
	module = Module.objects.get(module_name = name)
	function = module.function_set.get(func_name = func_name.replace("_"," "))
	app = module.application
	threads = int(module.module_threads)
	# path = os.path.join(robotCfg.TestPath,app.app_name,module.module_data)
	result = {}
	result['name'] = name
	# cfg = ConfigParser.RawConfigParser()
	# cfg.optionxform = str
	# cfg.read(path)
	setting = json.loads(function.func_setting)
	if ("filelist" in setting.keys()):
		files = setting["filelist"].split(",")
		table = []
		row = ["template"]
		for i in range(threads):
			row.append("thread " + str(i + 1))
		table.append(row)
		for file in files:
			row = []
			path = os.path.join(robotCfg.TestPath,app.app_name,"data",file)
			if (os.path.exists(path)):
				html = _getlink(file,name,label = file)
			else:
				html = _getlink(file,name, prefix=file)
			html = html + "|" + _getlink(file,name,label = "Upload", func = "uploadcsv")
			row.append(html)
			for i in range(threads):
				datafile = file[:file.find(".csv")] + "_" + str(i + 1) + ".csv"
				path = os.path.join(robotCfg.TestPath,app.app_name,"data",datafile)
				if (os.path.exists(path)):
					row.append(_getlink(datafile,name,label=datafile))
				else:
					row.append(_getlink(datafile,name))
			table.append(row)
		result["data"] = table
	else:
		result["data"] = None
	return HttpResponse(json.dumps(result), content_type="application/json")

def threaddatatable(request):
	name = request.GET["module"]
	func_name = request.GET["func_name"]
	module = Module.objects.get(module_name = name)
	app = module.application
	threads = int(module.module_threads)
	function = module.function_set.get(func_name = func_name.replace("_", " "))
#	path = os.path.join(robotCfg.TestPath,app.app_name,module.module_data)
	result = {}
	result['name'] = name
#	cfg = ConfigParser.RawConfigParser()
#	cfg.optionxform = str
#	cfg.read(path)
	setting = json.loads(function.func_setting)
	files = setting["thread-datalist"].split(",")
	table = []
	row = ["Data file For Threads"]
	table.append(row)
	for file in files:
		row = []
		path = os.path.join(robotCfg.TestPath,app.app_name,"data",file)
		if (os.path.exists(path)):
			html = _getlink(file,name,label = file)
		else:
			html = _getlink(file,name, prefix=file)
		html = html + "|" + _getlink(file,name,label = "Upload", func = "uploadcsv")
		row.append(html)
		table.append(row)
	result["data"] = table
	return HttpResponse(json.dumps(result), content_type="application/json")

	

def _getlink(file,name,label="Create",func="editcsv", prefix=""):
	html = prefix + "<a href=\"/performance/{func}?file={file}&module={name}\" target=\"popup\" onclick=\"window.open('/performance/{func}?file={file}&module={name}','Data File','width=800,height=600')\"><u>{label}</u></a>".format(func=func,file=file,name=name,label=label)

	return html
	
def editcsv(request):
	name = request.GET['module']
	module = Module.objects.get(module_name = name)
	app = module.application
	file = request.GET['file']
	context = {'app':app.app_name,'data_file':file,'module':name, 'is_popup': True}
	return render(request, 'performance/file.html', context)
	
def loadcsv(request):
	app = request.GET["app"]
	datafile = request.GET["file"]
	m = re.search('(.+)_\d+.csv$',datafile)
	module = request.GET["module"]
	path = os.path.join(robotCfg.TestPath,app,"data",datafile)
	if (os.path.exists(path)):
		data = csv.DictReader(open(path,"r"))
	else:
		if (m):
			path = os.path.join(robotCfg.TestPath,app,"data", m.group(1) + ".csv")
			if (os.path.exists(path)):
				data = csv.DictReader(open(path,"r"))
			else:
				data = None
		else:
			data = None
	result={}
	if (data):
		if (_threadFile(module,datafile)):
			result["thread"] = True;
			result["data"] = [_urlDecode("NONE",l) for l in data]
		else:
			result["data"] = [l for l in data]
		result["header"] = data.fieldnames
	else:
		result["header"] = None
		result["data"] = None
	return HttpResponse(json.dumps(result), content_type="application/json")	

def savecsv(request):
	if (request.GET):
		app = request.GET["app"]
		datafile = request.GET["file"]
		module = request.GET["module"]
		isthreadfile = _threadFile(module,datafile)
		path = os.path.join(robotCfg.TestPath,app,"data",datafile)
		if (os.path.exists(path)):
			backup_path = path + ".bak"
			shutil.copy(path, backup_path)
		data = json.loads(request.body)
		header = data["header"]
		sheetdata = data["data"]
		csv_file = open(path,"w")
		csv_file.write(",".join(header) + "\n");
		for line in sheetdata:
			if (line and line[0]):
				if (isthreadfile):
					data_line = map(lambda x: "" if (x == None) else urllib.quote_plus(x), line)
				else:
					data_line = map(lambda x: "" if (x == None) else x, line)
				csv_file.write(",".join(data_line) + "\n")
		result = "OK"
		return HttpResponse(json.dumps(result), content_type="application/json")
	#Save uploaded file
	if (request.POST):
		app = request.POST["app"]
		datafile = request.POST["file"]
		for file in request.FILES.keys():
			path = os.path.join(robotCfg.TestPath,app,"data",datafile)
			csv_file = open(path,"w")
			f = request.FILES[file]
			for chunk in f.chunks():
				csv_file.write(chunk)
			csv_file.close()
			context={'data_file':datafile}
		return render(request, 'performance/close.html',context)

def _threadFile(module, datafile):
	m = Module.objects.get(module_name = module)
	app = m.application.app_name
	path = os.path.join(robotCfg.TestPath,app,m.module_data)
	cfg = ConfigParser.RawConfigParser()
	cfg.read(path)
	if (cfg.has_option("common","thread-datalist")):
		datalist = cfg.get("common","thread-datalist")
		if (datalist.find(datafile) >=0):
			return True
	return False
		
def uploadcsv(request):
	name = request.GET['module']
	module = Module.objects.get(module_name = name)
	app = module.application
	file = request.GET['file']
	context = {'app':app.app_name,'data_file':file,'module':name, 'is_popup': True}
	return render(request, 'performance/upload.html', context)

def loadtree(request):
	root = {}
	root["name"] = robotCfg.ProjectName
	root["type"] = "Project"
	root["childtype"] = "Application"
	root["description"] = robotCfg.description
	apps = []
	for app in Application.objects.all().filter(is_deleted = 'N'):
		anode = {}
		anode["name"] = app.name
		anode["type"] = "Application"
		anode["description"] = app.description
		anode["childtype"] = "Module"
		anode["id"] = app.id
		modules=[]
		for module in app.module_set.all().filter(is_deleted = 'N'):
			mnode = {}
			mnode["name"] = module.name
			mnode["type"] = "Module"
			mnode["childtype"] = "Function"
			mnode["description"] = module.description
			mnode["id"] = module.id
			funcs = []
			for func in module.function_set.all().filter(is_deleted = 'N'):
				fnode = {}
				fnode["name"] = func.name
				fnode["type"] = "Function"
				fnode["childtype"] = "Scenario"
				fnode["description"] = func.description
				fnode["id"] = func.id
				scenarios = [] 
				for scenario in func.scenario_set.all().filter(is_deleted = 'N'):
					snode = {}
					snode["name"] = scenario.name
					snode["type"] = "Scenario"
					snode["id"] = scenario.id
					snode["description"] = scenario.description
					snode["resource"] = scenario.resource
					snode["setting"] = json.loads(scenario.settings)
					snode["children"] = []
					scenarios.append(snode)
				fnode["children"] = scenarios
				funcs.append(fnode)
			mnode["children"] = funcs
			modules.append(mnode)
		anode["children"] = modules
		apps.append(anode)
	root["children"] = apps
	data = {}
	data["data"] = root
	data["hierarchy"] = ["Project","Application","Module","Function","Scenario","Test Case"]
	return HttpResponse(json.dumps(data), content_type="application/json")			
	
def savevar(request):
	name = request.POST['varName']
	value = request.POST['varValue']
	appName = request.POST['appName']
	apps = []
	if appName == "all":
		apps = Application.objects.all()
	else:
		apps = [ Application.objects.get(app_name=appName)]
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			if (name in robotCfg.ModuleVars):
				if (name == "threads"):
					module.module_threads = int(value)
				elif (name == "ramp"):
					module.module_ramp_up = int(value)
				elif (name == "server"):
					module.module_target = value
				else:
					module.module_loop = int(value)
				module.save()
			else:
				for function in module.function_set.all():
					setting = json.loads(function.func_setting)
					if name in setting.keys():
						setting[name] = value
						function.func_setting = json.dumps(setting)
						function.save()
	
	return HttpResponse(json.dumps("OK"), content_type="application/json")
	
def admin(request):
	context = {'projectName':robotCfg.ProjectName, 'tags': Tag.objects.all()}
	return render(request, 'automation/admin.html', context)

def exectests(request):
	data = json.loads(request.body)
	machine = TestMachine.objects.get(label = data["machine"])
	priority = 5
	if ("priority" in data.keys()):
		priority = int(data["priority"])
	ts = time.time()
	ts_f = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M")
#	import pdb;pdb.set_trace()
	for item in data["tests"]:
		module = item["module"]
		func = item["func"]
		m = Module.objects.get(module_name=module)
		func_name = func.replace("_", " ")
		function = m.function_set.get(func_name = func_name)
		appname = m.application.app_name

		testRun = TestRun(module=m,target=m.module_target,func_name=func,ts_string=ts_f,result="Queued",priority=priority,machine=machine)
		testRun.save()
		queues.put(testRun.target, testRun)
	return HttpResponse(json.dumps("OK"), content_type="application/json")	

def loadanalysis(request):
	resultset = {}
	print datetime.datetime.now().strftime("%H:%M:%S")
	if "analysis" in request.GET.keys():
		samedate = True
		id = request.GET["analysis"];		
		analysis = Analysis.objects.get(id = int(id))
		analysis_set = [analysis]
		module = analysis.module
		if request.GET["scope"] == "app":
			app = module.application
			analysis_set = Analysis.objects.filter(module__in=app.module_set.all()).filter(brief = analysis.brief)
			
		if ("from" not in request.GET.keys() or "to" not in request.GET.keys()):
			results = get_analysis_results(analysis_set)
		else:
			if not request.GET["from"] == request.GET["to"]:
				samedate = False
			fromDate = datetime.datetime.strptime(request.GET["from"],"%Y-%m-%d")
			toDate = datetime.datetime.strptime(request.GET["to"],"%Y-%m-%d") + datetime.timedelta(hours=24)
			results = get_analysis_results(analysis_set,fromDate,toDate)
		resultset["name"] = analysis.name
		resultset["id"] = str(analysis.id)
		resultset["label"] = results[0]["label"]
		resultset["group"] = []
		for result in results:
			resultset["group"] = resultset["group"] + result["group"]
		resultset["types"] = results[0]["types"]
		resultset["start_time"] = results[0]["start_time"]
		resultset["location"] = results[0]["location"]
		resultset["module"] = [a.module.module_name for a in analysis_set]
		if not samedate:
			datas = {}
			new_groups = []
			for group in resultset["group"]:
				key = group["ts_string"].split("_")[0] + "|" + group["module"] + "|" + group["name"] + "|" + group["machine"] 
				
				if key in datas.keys():
					datas[key].append(group)
				else:
					datas[key] = [group]
			keys = datas.keys()
			keys.sort()
			for key in keys:
				count = 0			
				average = []
				for label in resultset["label"]:
					sum = 0
					nonecount = 0
					for group in datas[key]:
						if (group["data"][count] and count < len(group["data"])):
							sum = sum + int(group["data"][count])
						else:
							nonecount = nonecount + 1
					average.append(sum/(len(datas[key]) - nonecount))
					count = count + 1
				new_group={}
				new_group["ts_string"],new_group["module"],new_group["name"],new_group["machine"]=key.split("|")
				new_group["failed"] = 0
				new_group["data"] = average
				new_group["func_name"] = datas[key][0]["func_name"]
				
				for group in datas[key]:
					new_group["failed"] = new_group["failed"] + group["failed"]
				new_groups.append(new_group)
			resultset["group"] = new_groups
			resultset["start_time"] = []
			for group in new_groups:
				if group["ts_string"] not in resultset["start_time"]:
					resultset["start_time"].append(group["ts_string"])
			for item in resultset["group"]:
				item["red"] = int(random.random() * 255)
				item["green"] = int(random.random() * 255)
				item["blue"] = int(random.random() * 255)
				if item["red"] + item["green"] + item["blue"] > 600:
					item["red"] = 255 - item["red"]
					item["green"] = 255 - item["green"]
					item["blue"] = 255 - item["blue"]
			resultset["samedate"] = samedate
						

	print datetime.datetime.now().strftime("%H:%M:%S")
	return HttpResponse(json.dumps(resultset), content_type="application/json")
		
	
	
def check(request):	
	if "module" in request.GET.keys():
		module_name = request.GET['module']
		module = Module.objects.get(module_name = module_name)
		analysis_set = module.analysis_set.all()
		title_name = module_name
		scope = "module"
	elif "app" in request.GET.keys():
		app = Application.objects.get(app_name = request.GET['app'])
		analysis_set = Analysis.objects.filter(module__in = app.module_set.all())
		title_name = app.app_name
		scope = "app"
		
		
	results = []
	ids = []
	num = 1
	briefs = []
	for analysis in analysis_set:
		item = {}
		item["name"] = analysis.brief
		item["id"] = "analysis_" + str(analysis.id)
		item["hours"] = analysis.filter.split("=")[1]
		if (analysis.brief not in briefs):
			briefs.append(analysis.brief)
			ids.append(analysis.id)
			results.append(item)
	context = {"results":results,"title": "Performance Analysis for " + title_name,"ids":ids,"scope":scope}
	return render(request, 'performance/check.html', context)
	
def get_analysis_results(analysis_set,fromDate =None,toDate=None):

	results = []
	num = 1
	for analysis in analysis_set:
		func_name = analysis.func_name
		policy = analysis.group.strip()
		filter = getDateDelta(analysis.filter)
		module = analysis.module
		if (fromDate and toDate):
			testRuns = module.testrun_set.filter(func_name = func_name).filter(timestamp__gte = fromDate).filter(timestamp__lte = toDate).exclude(result = "running")			
		else:
			testRuns = module.testrun_set.filter(func_name = func_name).filter(timestamp__gt = datetime.datetime.now() - filter).exclude(result = "running")
		
		resultset = {}
		resultset["kin"] = analysis.brief
		resultset["name"] = analysis.name
		resultset["id"] = "analysis_" + str(num)
		resultset["label"] = []
		resultset["group"] = []
		resultset["types"] = []
		resultset["start_time"] = []
		resultset["location"] = []
		resultset["modules"] = [module.module_name]

		testreports = TestReport.objects.filter(testrun__in = testRuns)

			
		
		for testRun in testRuns:
			runset = {}
			runset["group"] = []
			for testReport in testreports:
				if testReport.testrun_id == testRun.id:
					if testReport.sample_name.find(">>") > 0:
						label = testReport.sample_name.split(">>")[1].strip()
						#import pdb;pdb.set_trace()
						m = re.match(policy,label)
						if m:
							group = m.group("group").strip()
							name = m.group("name").strip()
							if group not in runset["group"]:
								runset["group"].append(group)
								runset[group] = {}
								runset[group]["_failed"] = 0
							runset[group][name] = testReport.response_time
							if testReport.result == "false":
								runset[group]["_failed"] = runset[group]["_failed"] + 1
							if name not in resultset["label"]:
								resultset["label"].append(name)
			runset["ts_string"] = testRun.ts_string
			runset["machine"] = testRun.machine.label
			for group in runset["group"]:
				groupset = {}
				groupset["ts_string"] = testRun.ts_string
				groupset["machine"] = testRun.machine.label.replace(" ","_")
				groupset["data"] = []
				for key in resultset["label"]:
					if (key in runset[group].keys()):
						groupset["data"].append(runset[group][key])
					else:
						groupset["data"].append(None)
				groupset["failed"] = runset[group]["_failed"]
				groupset["name"] = group
				groupset["func_name"] = func_name
				groupset["module"] = module.module_name
				if group not in resultset["types"]:
					resultset["types"].append(group)
				if testRun.ts_string not in resultset["start_time"]:
					resultset["start_time"].append(testRun.ts_string)
				if testRun.machine.label.replace(" ","_") not in resultset["location"]:
					resultset["location"].append(testRun.machine.label.replace(" ","_"))
				resultset["group"].append(groupset)
			
		total = len(resultset["group"])
		pre = {}
		pre["red"] = 0
		pre["green"] = 0
		pre["blue"] = 0
		for item in resultset["group"]:
			item["red"] = int(random.random() * 255)
			item["green"] = int(random.random() * 255)
			item["blue"] = int(random.random() * 255)
			if item["red"] + item["green"] + item["blue"] > 600:
				item["red"] = 255 - item["red"]
				item["green"] = 255 - item["green"]
				item["blue"] = 255 - item["blue"]
			
		results.append(resultset)
		num = num + 1
	return results
	
def analysis(request):
	if "module" in request.GET.keys():
		module_name = request.GET['module']
		module = Module.objects.get(module_name = module_name)
		analysis_set = module.analysis_set.all()
		title_name = module_name
	elif "app" in request.GET.keys():
		app = Application.objects.get(app_name = request.GET['app'])
		analysis_set = Analysis.objects.filter(module__in = app.module_set.all())
		title_name = app.app_name
		
	results = get_analysis_results(analysis_set)
	new_results = []
	count = 0
	label_set = {}
	for result in results:
		if result["kin"] not in label_set.keys():
			label_set[result["kin"]] = [count]
		else:
			label_set[result["kin"]].append(count)
		count = count + 1
		
	for key in label_set.keys():
		module_set = label_set[key]
		for i in module_set[1:]:
			results[module_set[0]]["modules"] = results[module_set[0]]["modules"] + results[i]["modules"]
			results[module_set[0]]["group"] = results[module_set[0]]["group"] + results[i]["group"]
		new_results.append(results[module_set[0]])
	
	context = {"results" : new_results, "title": "Performance Analysis for " + title_name}
	return render(request, 'performance/analysis.html', context)
	

def getDateDelta(filter):
	arg_name = filter.split('=')[0]
	value = int(filter.split('=')[1])
	if arg_name.strip() == 'days':
		return datetime.timedelta(days=value)
	elif arg_name.strip() == 'hours':
		return datetime.timedelta(hours=value)
		
# def loadnode(request):
	# type = request.GET["type"]
	# node = {}
	# if (type == "project"):
		# node["type"] = "Project"
		# node["name"] = robotCfg.projectName
		# node["description"] = robotCfg.projectDescription
		# node
		
def detail(request):
	pass