
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
from performance.models import *
from multiprocessing import Process,Queue
from django.contrib.auth.decorators import login_required

from performance.Queues import queues
from config import perfCfg
from performance.utils import generate_report
import os, json, csv, urllib,re
import ConfigParser,shutil,subprocess,time,datetime


#TestPath = "c:\\SAILIS\\"
#JMeterPath = "C:\\apache-jmeter-2.10\\bin\\jmeter.bat"
#JMeterHeader = ['Time Stamp', 'Response Time','Sample Name','Response Code','Response Message','Thread Name','Type','Result','Bytes','URL','Latency']
#ReportHeader = ['Sample Name','Result','Time Stamp', 'Response Time','Response Code','Response Message','Type','URL','Bytes','Latency']


	
def index(request):
	apps = Application.objects.all()
	context = {'apps':apps, 'varList':perfCfg.ModuleVars + perfCfg.DataVars}
	return render(request, 'performance/index.html', context)
	
def loadapps(request):
	apps = Application.objects.all()
	results = []
	
	for app in apps:
		result = {}
		result['name'] = app.app_name
		result['modules'] = []
		for module in app.module_set.all():
			m = {}
			m['name'] = module.module_name
			m['scenarios'] = []
			for scenario in module.scenario_set.all():
				s = {}
				s['name'] = scenario.scenario_name;
				s['data_file'] = scenario.scenario_data;
				m['scenarios'].append(s)
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
	tags = None
	if ("priority" in request.GET.keys()):
		priority = int(request.GET["priority"])
	else:
		priority = 5
	if ("tag" in request.GET.keys()):
		tag_names = request.GET["tag"].split(",")
		tags = []
		for tag_name in tag_names:
			tag = Tag.objects.get(tag_name = tag_name)
			tags.append(tag)
	if ("runname" in request.GET.keys()):
		runname = request.GET["runname"]
	else:
		runname = None
	if ("release" in request.GET.keys()):
		release = request.GET["release"]
	else:
		release = None
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
#			path = os.path.join(perfCfg.TestPath,app.app_name, module.module_data);
#			cfg = ConfigParser.RawConfigParser()
#			cfg.optionxform = str
#			cfg.read(path)
#			functions = cfg.get("common","functions")
			for func in module.function_set.all():
				f = {}
				testRun = None
				f["name"] = func.func_name.replace(" ","_")
				testRuns = module.testrun_set.filter(func_name = f["name"]).order_by("-ts_string")
				if (release):
					selectedRelease = Release.objects.get(name = release)
					testRuns = testRuns.filter(release = selectedRelease)
				if (runname):
					testRuns = testRuns.filter(name = runname)
					
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
					if (tags):
						samples = scenario.sample_set.filter(priority__lte = priority,is_deleted='N',tags__in=tags)
					else:
						samples = scenario.sample_set.filter(priority__lte = priority,is_deleted='N')
					if testRun:
						for sample in samples:
							try:
								testReports = sample.testreport_set.filter(func_name=testRun.func_name,ts_string=testRun.ts_string)
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
	res['name'] = perfCfg.ProjectName
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

def loadrelease(request):
	if ("release" in request.GET.keys()):
		Name = request.GET["release"]
		release = Release.objects.get(name=Name)
		name_list = release.testrun_set.all().order_by("-ts_string").values("name").distinct()
	else:
		name_list = TestRun.objects.all().order_by("-ts_string").values("name").distinct()
	runs_list = [x["name"] for x in name_list]
	return HttpResponse(json.dumps(runs_list), content_type="application/json")
		
def loaddata(request):
	app = request.GET["app"]
	func = request.GET["func"]
	module = request.GET["module"]
	scenario = request.GET["scenario"]
	a = Application.objects.get(app_name=app)
	m = a.module_set.get(module_name = module)
	func = func.replace("_"," ")
	f = m.function_set.get(func_name=func)
	s = f.scenario_set.get(scenario_name=scenario)
	rawdata = []
	if s.sample_set.count() == 0:
		path = os.path.join(perfCfg.TestPath,app,"data",s.scenario_data)
		header = open(path,"r").readlines()[0].strip("\n").split(",")
		rawdata = [x for x in csv.DictReader(open(path,"r"))]
		_unique_sample_name(rawdata)
		line_no = 1
		for item in rawdata:
			item = _urlDecode(s,item)
			line = ",".join([item[x] for x in header])
			sample = Sample(sample_name=item['sample'],is_deleted='N',sample_value= line,line_no = line_no,priority=5,scenario=s)
			sample.save()
			line_no = line_no + 1
		s.scenario_header = ",".join(header)
		s.save()
		sample = Sample(sample_name="others",is_deleted='Y',priority=5,scenario=s,sample_value="None")
		sample.save()
	
	data = []
	for sample in s.sample_set.filter(is_deleted='N').order_by('line_no'):
		item = dict(zip(s.scenario_header.split(","),sample.sample_value.split(",")))
		item = _urlDecode(s,item)
		if (sample.sample_name != item['sample']):
			sample.sample_name = item['sample']
			sample.save()
		values = sample.sample_value.split(",")
		if (values[0] != item['sample']):
			values[0] = item['sample']
			sample.sample_value = ",".join(values)
			sample.save()
			
		item['dinos_pkid'] = str(sample.id)
		item['$Priority$'] = str(sample.priority)
		tags = [tag.tag_name for tag in sample.tags.all()]
		item['$Tag$'] = ",".join(tags)
		data.append(item)
		
	
	result={}
	result["data"] = data
	_unique_sample_name(result["data"])
#	if '$Priority$' not in data.fieldnames:
#		data.fieldnames.append('$Priority$')
	headers = s.scenario_header.split(",")
	headers.append('$Priority$')
	headers.append('$Tag$')
	result["header"] = headers
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
				dict[key] = urllib.unquote_plus(dict[key])
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
	path = os.path.join(perfCfg.TestPath,app,"report",datafile)
	csvFile = open(path,"r")
	data_list = []
	for line in csvFile.readlines():
		data = {}
		items = line.split(",")
		i = 0
		for header in perfCfg.JMeterHeader:
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
	result["header"] = perfCfg.ReportHeader
	return result

	
def loadscenario(request):
	app = request.GET["app"]
	module = request.GET["module"]
	func = request.GET["func"]
	scenario = request.GET["scenario"]
	is_popup = True
	context = {'app':app,'func':func,'scenario':scenario,'module':module, 'tags': Tag.objects.all(),'is_popup': is_popup}
	return render(request, 'performance/data.html', context)
	
def loadcfg(request):
	app = request.GET["app"]
	module = request.GET["module"]
	a_module = Module.objects.get(module_name=module);
	if ("func" in request.GET.keys()):
		func_name = request.GET["func"].replace("_"," ");
		function = a_module.function_set.get(func_name = func_name)
	else:
		function = a_module.function_set.all()[0]
	# path = os.path.join(perfCfg.TestPath,app, a_module.module_data);
	# cfg = ConfigParser.RawConfigParser()
	# cfg.optionxform = str
	# cfg.read(path)
	data = {}
	setting = json.loads(function.func_setting)
	for (key,value) in setting.items():
		data[key] = value
	funcs = [func.func_name for func in a_module.function_set.all()]
	data["functions"] = ",".join(funcs)
	# for (key,value) in  cfg.items("common"):
		# data[key] = value
	m_info = {}
	m_info["Server to be tested"] = a_module.module_target
	m_info["threads number"] = a_module.module_threads
	m_info["loop number"] = a_module.module_loop
	m_info["ramp up seconds"] = a_module.module_ramp_up
	
	result = {}
	result["func"] = function.func_name
	result["app"] = app
	result["data"] = data
	result["name"] = module
	result["module"] = m_info
	return HttpResponse(json.dumps(result), content_type="application/json")
	
def savedata(request):
	app = request.GET["app"]
	func = request.GET["func"]
	module = request.GET["module"]
	s_name = request.GET["scenario"]
	a = Application.objects.get(app_name=app)
	m = a.module_set.get(module_name = module)
	func = func.replace("_"," ")
	f = m.function_set.get(func_name=func)
	scenario = f.scenario_set.get(scenario_name=s_name) 
	path = os.path.join(perfCfg.TestPath,app,"data",scenario.scenario_data)
	backup_path = path + ".bak"
	if (os.path.exists(path)):
		shutil.copy(path, backup_path)
	data = json.loads(request.body)
	header = data["header"][:-2]
	sheetdata = data["data"]
	dbChanges = data["changes"]
	csv_file = open(path,"w")
	csv_file.write(",".join(header) + "\n");
	minRemove_line = len(sheetdata)
	for pkid in dbChanges["removeList"]:
		sample = Sample.objects.get(id=int(pkid))
		if minRemove_line > sample.line_no:
			minRemove_line = sample.line_no
		sample.is_deleted = 'Y'
		sample.save()
#	scenario.sample_set.filter(is_deleted='N').update(is_deleted='Y')
	line_no = 1
	insert_lines = 0
	for line in sheetdata:

		if line and line[0]:		
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
			data_line = map(lambda x: "" if (x == None) else urllib.quote_plus(str(x)), line[1:len(header)])
			data_line.insert(0,line[0])
			value = ",".join(data_line)
			if (len(line) > len(header)):
				dinos_pkid = line[-1]
				if (not dinos_pkid):
					sample = Sample(sample_name = line[0],scenario=scenario,priority=int(line[-2]),sample_value=value,line_no = line_no, is_deleted='N')
					insert_lines = insert_lines + 1
					sample.save()				
				elif (dinos_pkid in dbChanges["changeList"] or insert_lines > 0 or line_no > minRemove_line):
					sample=Sample.objects.get(id=int(dinos_pkid))
					sample.sample_name = line[0]
					sample.priority = int(line[-3])
					tagsValue = line[-2].strip()
					tags = tagsValue.split(",")
					original_tags= [tag.tag_name for tag in sample.tags.all()]
					for tag in tags:
						if len(tag) > 0 and tag not in original_tags:
							sample.tags.add(Tag.objects.get(tag_name=tag))
					for tag in original_tags:
						if tag not in tags:
							sample.tags.remove(Tag.objects.get(tag_name=tag))
					sample.line_no = line_no
					sample.sample_value = value
					sample.is_deleted='N'
					sample.save()
			else:
				sample = Sample(sample_name = line[0],scenario=scenario,priority=int(line[-2]),sample_value=value,line_no = line_no, is_deleted='N')
				sample.save()
			line_no = line_no + 1	
			csv_file.write( value + "\n")
	
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
#	path = os.path.join(perfCfg.TestPath,app,module.module_data)
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
	result["thread_datalist"] = "thread_datalist" in setting.keys()
	return HttpResponse(json.dumps(result), content_type="application/json")

def loadstatus(request,module,func):
	result={}
	result["func"] = func
	result["module"] = module
	path = os.path.join(perfCfg.TestPath,"lock",".".join([module,func,"lock"]))
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
	if ("priority" in request.GET.keys()):
		priority = int(request.GET["priority"])
	else:
		priority = 5

		
	timestamp = items[0] + " " + items[1].replace("-",":")
	
	#try:
	testRun = TestRun.objects.get(func_name = func, ts_string = ts)
	testReports = TestReport.objects.filter(func_name = func, ts_string = ts)
	target = testRun.target
	module = testRun.module
	if ("scenario" in request.GET.keys()):
		scenario = urllib.unquote_plus(request.GET["scenario"])
	
	reports = []
	for testReport in testReports:
		reports.append(testReport.JMeterDict())
	app = module.application
	report_file = ".".join([module.module_name,func,ts,"csv"])
#	report_path = os.path.join(perfCfg.TestPath, app.app_name,"report", report_file)
#	result = loadreport(app.app_name, report_file)
	data = []
	for line in reports:
		data_line = []
		for item in perfCfg.ReportHeader:
			data_line.append(line[item])
			
		if (data_line[0].find(scenario) >= 0 ):
			if (priority and type(line['Priority']) == type(1)):
				if (line['Priority'] <= priority):
					data.append(data_line)
			else:	
				data.append(data_line)
	title = scenario
	if len(title) == 0:
		title = func
	context = { 'is_popup': True, 'reportFile': report_file, 'app': app.app_name, 
		'report_name': 'Performance test report for ' + title,'time_stamp':timestamp,'target':target,
		'data':data,
		'header': perfCfg.ReportHeader
		}
	return render(request, 'performance/report.html', context)
	#except Exception as e:
	#	context = { 'is_popup': True, 'errMsg': str(e)}
	#	return render(request, 'performance/error.html', context)
		
def log(request, func):
	ts = request.GET["ts"]
	testRun = TestRun.objects.get(func_name = func, ts_string = ts)
	module = testRun.module
	app = module.application
	log_file = ".".join([module.module_name,func,ts,"log"])
	log_path = os.path.join(perfCfg.TestPath, app.app_name,"log", log_file)
	try:
		f = open(log_path, "r")
		messages = f.readlines()
		f.close()
		context = { 'is_popup': True, 'logFile': log_file, 'app': app.app_name, 'log_name': 'Jmeter log for ' + func, 'msgs': messages }
		return render(request, 'performance/log.html', context)

	except Exception as e:
		context = { 'is_popup': True, 'errMsg': str(e)}
		return render(request, 'performance/error.html', context)

def exectests(request):
	data = json.loads(request.body)
	priority = 5
	if ("priority" in data.keys()):
		priority = int(data["priority"])
	if ("runname" in data.keys()):
		runname = data["runname"].strip()
	else:
		runname = None
	if ("release" in data.keys()):
		release_name = data["release"].strip()
		release = Release.objects.get(name = releaese_name)
	else:
		release = Release.objects.all().order_by('-name')[0]
	tags = []
	if ("tags" in data.keys()):
		tag_list = data["tags"].split(",")
		for tag in tag_list:
			tags.append(Tag.objects.get(tag_name = tag))
			
	ts = time.time()
	ts_f = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M")
	samples = Sample.objects.all()
	for item in data["tests"]:
		module = item["module"]
		func = item["func"]
		m = Module.objects.get(module_name=module)
		func_name = func.replace("_", " ")
		function = m.function_set.get(func_name = func_name)
		if (len(tags) > 0):
			sample_num = samples.filter(scenario__in = function.scenario_set.all()).filter(tags__in = tags).count()
		else:
			sample_num = 1
		appname = m.application.app_name
		if not runname or len(runname) == 0:
			runname = ts_string
		if sample_num > 0:
			testRun = TestRun(module=m,target=m.module_target,func_name=func,ts_string=ts_f,result="Queued",priority=priority,name=runname,release = release)
			testRun.save()
			queues.put(testRun.target, testRun)
	return HttpResponse(json.dumps("OK"), content_type="application/json")	
		
def runtest(request):
	data = json.loads(request.body)
	module = data["module"]
	func = data["func"]
	priority = 5
	if ("priority" in data.keys()):
		priority = int(data["priority"])
	 
	ts = time.time()
	ts_f = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M")
	m = Module.objects.get(module_name=module)
	func_name = func.replace("_", " ")
	function = m.function_set.get(func_name = func_name)
	appname = m.application.app_name

	testRun = TestRun(module=m,target=m.module_target,func_name=func,ts_string=ts_f,result="Queued",priority=priority)
	testRun.save()
	
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
	module = testRun.module
	name = module.module_name
	func = testRun.func_name
	ts_f = testRun.ts_string
	_createLock(module.module_name,func)
	try:
		testRun.result = "running"
		testRun.save()
		app = module.application
		testplan_path = os.path.join(perfCfg.TestPath, app.app_name,module.module_testplan)
		testlog_path = os.path.join(perfCfg.TestPath, app.app_name,"log", ".".join([name,func,ts_f,"log"]))
		testreport_path = os.path.join(perfCfg.TestPath, app.app_name,"report", ".".join([name,func,ts_f,"csv"]))
#		testcfg_path = os.path.join(perfCfg.TestPath, app.app_name, module.module_data)
		func_name = testRun.func_name.replace("_", " ")
		function = module.function_set.get(func_name = func_name)
		for scenario in function.scenario_set.all():
			datapath = os.path.join(perfCfg.TestPath,app.app_name,"data",scenario.scenario_data)
			csv_file = open(datapath,"w")
			csv_file.write(scenario.scenario_header + "\n")
			samples = scenario.sample_set.filter(is_deleted="N",priority__lte=testRun.priority).order_by("line_no")
			for sample in samples:
				csv_file.write(sample.sample_value + "\n")
			csv_file.close()
		setting = json.loads(function.func_setting)
		# cfg = ConfigParser.RawConfigParser()
		# cfg.optionxform = str
		# cfg.read(testcfg_path)
		arg_list = [perfCfg.JMeterPath, "-n","-t" + testplan_path, "-j" + testlog_path, "-l" + testreport_path]
		arg_list.append("-JTOTAL="+str(module.module_threads))
		arg_list.append("-JLOOP="+str(module.module_loop))
		arg_list.append("-JRAMPUP="+str(module.module_ramp_up))
		arg_list.append("-JTARGET="+module.module_target)
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
		_removeLock(name,func)
	
	
	except Exception as e:
		testRun.result = "exception"
		testRun.message = str(e)
		testRun.save()
		_removeLock(name,func)
		
	return testRun.result

def populate_report(module,testRun, report_path):

	csvFile = open(report_path,"r")
	reader = csv.DictReader(csvFile, fieldnames = perfCfg.JMeterHeader)
	
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
					testReport = TestReport(func_name=testRun.func_name,sample_name=sample_name,response_time=data['Response Time'],URL=data['URL'],timestamp=time_stamp,response_code = data['Response Code'],ts_string=testRun.ts_string,target=testRun.target,result=data['Result'],message=data['Response Message'],sample=sample,type=data['Type'],thread_name=data['Thread Name'],latency=data['Latency'],bytes=data['Bytes'])
					testReport.save()
					isCreated = True
					break
			if not isCreated:
				sample = scenario.sample_set.get(sample_name="others")
				testReport = TestReport(func_name=testRun.func_name,sample_name=sample_name,response_time=data['Response Time'],URL=data['URL'],timestamp=time_stamp,response_code = data['Response Code'],ts_string=testRun.ts_string,target=testRun.target,result=data['Result'],message=data['Response Message'],sample=sample,type=data['Type'],thread_name=data['Thread Name'],latency=data['Latency'],bytes=data['Bytes'])
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
	path = os.path.join(perfCfg.TestPath,"lock",".".join([name,func,"lock"]))
	if (os.path.isfile(path)):
		raise Exception("Only allow one instance running for one function")
	file = open(path,"w")
	file.write(str(os.getpid()))
	file.close()

def _removeLock(name,func):
	path = os.path.join(perfCfg.TestPath,"lock",".".join([name,func,"lock"]))
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
			# path = os.path.join(perfCfg.TestPath,aName,module.module_data)
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
	
	ts_list = TestRun.objects.order_by("-ts_string").values("name").distinct()
	releases = Release.objects.all().order_by("-name")
	context = {'all_items':all_items, 'tags': Tag.objects.all(),'title' : "Performance Test Dashboard", 'ts_list':ts_list,'releases':releases}
	return render(request, 'performance/dashboard.html', context)
					
def loadfiletable(request):
	name = request.GET["module"]
	func_name = request.GET["func_name"] 
	module = Module.objects.get(module_name = name)
	function = module.function_set.get(func_name = func_name.replace("_"," "))
	app = module.application
	threads = int(module.module_threads)
	# path = os.path.join(perfCfg.TestPath,app.app_name,module.module_data)
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
			path = os.path.join(perfCfg.TestPath,app.app_name,"data",file)
			if (os.path.exists(path)):
				html = _getlink(file,name,label = file)
			else:
				html = _getlink(file,name, prefix=file)
			html = html + "|" + _getlink(file,name,label = "Upload", func = "uploadcsv")
			row.append(html)
			for i in range(threads):
				datafile = file[:file.find(".csv")] + "_" + str(i + 1) + ".csv"
				path = os.path.join(perfCfg.TestPath,app.app_name,"data",datafile)
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
#	path = os.path.join(perfCfg.TestPath,app.app_name,module.module_data)
	result = {}
	result['name'] = name
#	cfg = ConfigParser.RawConfigParser()
#	cfg.optionxform = str
#	cfg.read(path)
	setting = json.loads(function.func_setting)
	files = setting["thread_datalist"].split(",")
	table = []
	row = ["Data file For Threads"]
	table.append(row)
	for file in files:
		row = []
		path = os.path.join(perfCfg.TestPath,app.app_name,"data",file)
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
	path = os.path.join(perfCfg.TestPath,app,"data",datafile)
	if (os.path.exists(path)):
		data = csv.DictReader(open(path,"r"))
	else:
		if (m):
			path = os.path.join(perfCfg.TestPath,app,"data", m.group(1) + ".csv")
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
		path = os.path.join(perfCfg.TestPath,app,"data",datafile)
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
			path = os.path.join(perfCfg.TestPath,app,"data",datafile)
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
	path = os.path.join(perfCfg.TestPath,app,m.module_data)
	cfg = ConfigParser.RawConfigParser()
	cfg.read(path)
	if (cfg.has_option("common","thread_datalist")):
		datalist = cfg.get("common","thread_datalist")
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
	root["name"] = perfCfg.ProjectName
	root["type"] = "project"
	apps = []
	for app in Application.objects.all():
		anode = {}
		anode["name"] = app.app_name
		anode["type"] = "application"
		modules=[]
		for module in app.module_set.all():
			mnode = {}
			mnode["name"] = module.module_name
			mnode["type"] = "module"
			funcs = []
			for func in module.function_set.all():
				fnode = {}
				fnode["name"] = func.func_name
				fnode["type"] = "function"
				scenarios = [] 
				for scenario in func.scenario_set.all():
					snode = {}
					snode["name"] = scenario.scenario_name
					snode["type"] = "scenario"
					snode["children"] = []
					scenarios.append(snode)
				fnode["children"] = scenarios
				funcs.append(fnode)
			mnode["children"] = funcs
			modules.append(mnode)
		anode["children"] = modules
		apps.append(anode)
	root["children"] = apps
	return HttpResponse(json.dumps(root), content_type="application/json")			
	
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
			if (name in perfCfg.ModuleVars):
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
				# testcfg_path = os.path.join(perfCfg.TestPath, app.app_name, module.module_data)
				# cfg = ConfigParser.RawConfigParser()
				# cfg.optionxform = str
				# cfg.read(testcfg_path)
				# if cfg.has_option("common",name):
					# cfg.set("common",name,value)
					# backup_path = testcfg_path + ".bak"
					# shutil.copy(testcfg_path, backup_path)					
					# cfg_file = open(testcfg_path, "w");
					# cfg.write(cfg_file)
					# cfg_file.close()
	
	return HttpResponse(json.dumps("OK"), content_type="application/json")
	
def admin(request):
	context = {'projectName':perfCfg.ProjectName}
	return render(request, 'performance/admin.html', context)

def genreport(request):
	if "release" in request.GET.keys():
		release = Release.objects.get(name=request.GET["release"])
	else:
		release = Release.objects.all().order_by("-name")[0]
	if "runname" in request.GET.keys():
		runname = request.GET["runname"]
	else:
		runname = None
	
	generate_report(release,runname)
	
	freport=open("report.xlsx","rb")
	response = HttpResponse(freport,mimetype="application/vnd.ms-excel")
	response["Content-Disposition"] = "attachment; filename=report.xlsx"
	response["Content-Type"] = "application/vnd.ms-excel;charset=utf-8"
	return response
	
def detail(request):
	pass