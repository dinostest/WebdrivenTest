from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Max
from performance.models import Application, Module, TestRun
from multiprocessing import Process,Queue
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


from performance.Queues import queues
import os, json, csv, urllib
import ConfigParser,shutil,subprocess,time,datetime
# Author: Xiang Liu (liu980299@gmail.com)

TestPath = "c:\\SAILIS\\"
JMeterPath = "C:\\apache-jmeter-2.10\\bin\\jmeter.bat"
JMeterHeader = ['Time Stamp', 'Response Time','Sample Name','Response Code','Response Message','Thread Name','Type','Result','Bytes','URL','Latency']
ReportHeader = ['Sample Name','Result','Time Stamp', 'Response Time','Response Code','Response Message','Type','URL','Bytes','Latency']


	
def index(request):
	apps = Application.objects.all()
	context = {'apps':apps}
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
			path = os.path.join(TestPath,app.app_name, module.module_data);
			cfg = ConfigParser.RawConfigParser()
			cfg.optionxform = str
			cfg.read(path)
			functions = cfg.get("common","functions")
			for func in functions.split(","):
				f = {}
				testRun = None
				f["name"] = func.replace(" ","_")
				testRuns = module.testrun_set.filter(func_name = f["name"]).order_by("-timestamp")
				if (testRuns and len(testRuns) > 0):
					testRun = testRuns[0]
					f["status"] = testRun.result
				else:
					f["status"] = "initial"
				_set_status(m,f["status"])
				f["report"] = testRun.ts_string
				f["log"] = testRun.ts_string
				f["scenarios"] = []
				for scenario in module.scenario_set.all():
					s = {}
					s['name'] = scenario.scenario_name;
					s['data'] = scenario.scenario_data;
					s["status"] = testRun.result
					s["report"] = testRun.ts_string
					s["log"] = testRun.ts_string
					f['scenarios'].append(s)
				m['funcs'].append(f)
			_set_status(result,m["status"])
			result['modules'].append(m)
		_set_status(res,result['status'])
		results.append(result)
	res['data'] = results
	return HttpResponse(json.dumps(res), content_type="application/json")
	
def loaddata(request):
	app = request.GET["app"]
	datafile = request.GET["file"]
	scenario = request.GET["scenario"]
	path = os.path.join(TestPath,app,"data",datafile)
	data = csv.DictReader(open(path,"r"))
	result={}
	result["data"] = [_urlDecode(scenario, l) for l in data]
	result["header"] = data.fieldnames
	return HttpResponse(json.dumps(result), content_type="application/json")
	
def _urlDecode(scenario, dict):
	for key in dict.keys():
		if (not key == 'sample'):
			if (dict[key]):
				dict[key] = urllib.unquote_plus(dict[key])
			else:
				dict[key] = ""
	if dict['sample'].find(">>") <= 0:
		dict['sample'] = scenario + " >> " + dict['sample']
	else:
		dict['sample'] = scenario + " >> " + dict['sample'].split(">>")[1]
		
	return dict
	
def loadreport(app, datafile):
	path = os.path.join(TestPath,app,"report",datafile)
	csvFile = open(path,"r")
	data_list = []
	for line in csvFile.readlines():
		data = {}
		items = line.split(",")
		i = 0
		for header in JMeterHeader:
			data[header] = items[i]
			i = i+1
		if data['URL'] != 'null':
			data_list.append(data)
	
	result={}
	result["data"] = data_list
	result["header"] = ReportHeader
	return result

	
def loadscenario(request):
	app = request.GET["app"]
	datafile = request.GET["file"]
	scenario = request.GET["scenario"]
	is_popup = True
	context = {'app':app,'data_file':datafile,'scenario':scenario, 'is_popup': is_popup}
	return render(request, 'performance/data.html', context)
	
def loadcfg(request):
	app = request.GET["app"]
	module = request.GET["test"]
	a_module = Module.objects.get(module_name=module);
	path = os.path.join(TestPath,app, a_module.module_data);
	cfg = ConfigParser.RawConfigParser()
	cfg.optionxform = str
	cfg.read(path)
	data = {}
	for (key,value) in  cfg.items("common"):
		data[key] = value
	m_info = {}
	m_info["Server to be tested"] = a_module.module_target
	m_info["threads number"] = a_module.module_threads
	m_info["loop number"] = a_module.module_loop
	m_info["ramp up seconds"] = a_module.module_ramp_up
	
	result = {}
	result["data"] = data
	result["name"] = module
	result["module"] = m_info
	return HttpResponse(json.dumps(result), content_type="application/json")
	
def savedata(request):
	app = request.GET["app"]
	datafile = request.GET["file"]
	path = os.path.join(TestPath,app,"data",datafile)
	backup_path = path + ".bak"
	shutil.copy(path, backup_path)
	data = json.loads(request.body)
	header = data["header"]
	sheetdata = data["data"]
	csv_file = open(path,"w")
	csv_file.write(",".join(header) + "\n");
	for line in sheetdata:
		if line and line[0]:
			data_line = map(lambda x: "" if (x == None) else urllib.quote_plus(x), line[1:])
			data_line.insert(0,line[0])
			csv_file.write(",".join(data_line) + "\n")
	
	result = "OK"
	return HttpResponse(json.dumps(result), content_type="application/json")
	
	
def savecfg(request):
	app = request.GET["app"]
	name = request.GET["test"]
	module = Module.objects.get(module_name=name)
	data = json.loads(request.body)
	module.module_threads = data["module"]["threads number"]
	module.module_target = data["module"]["Server to be tested"]
	module.module_loop = data["module"]["loop number"]
	module.module_ramp_up = data["module"]["ramp up seconds"]
	module.save()
	path = os.path.join(TestPath,app,module.module_data)
	backup_path = path + ".bak"
	shutil.copy(path, backup_path)
	cfg_file = open(path, "r+");
	cfg = ConfigParser.RawConfigParser()
	cfg.optionxform = str
	cfg.read(path)
	for item in data["cfg"]:
		cfg.set("common",item["Key"],item["Value"])
	cfg.write(cfg_file)
	cfg_file.close()
	result={}
	result["module"]=module.module_name
	return HttpResponse(json.dumps(result), content_type="application/json")

def loadstatus(request,module,func):
	result={}
	result["func"] = func
	result["module"] = module
	path = os.path.join(TestPath,"lock",".".join([module,func,"lock"]))
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
	#try:
	testRun = TestRun.objects.get(func_name = func, ts_string = ts)
	module = testRun.module
	app = module.application
	report_file = ".".join([module.module_name,func,ts,"csv"])
	report_path = os.path.join(TestPath, app.app_name,"report", report_file)
	result = loadreport(app.app_name, report_file)
	data = []
	for line in result["data"]:
		data_line = []
		for item in ReportHeader:
			data_line.append(line[item])
		data.append(data_line)

	context = { 'is_popup': True, 'reportFile': report_file, 'app': app.app_name, 
		'report_name': 'Performance test report for ' + func,
		'data':data,
		'header': ReportHeader
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
	log_path = os.path.join(TestPath, app.app_name,"log", log_file)
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
	 
	ts = time.time()
	ts_f = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d_%H-%M")
	m = Module.objects.get(module_name=module)
	testRun = TestRun(module=m,target=m.module_target,func_name=func,ts_string=ts_f,result="Queued")
	#import pdb;pdb.set_trace()
	testRun.save()
	
	#_runtest(module,func,ts_f);
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
#	try:
	testRun.result = "running"
	testRun.save()
	app = module.application
	testplan_path = os.path.join(TestPath, app.app_name,module.module_testplan)
	testlog_path = os.path.join(TestPath, app.app_name,"log", ".".join([name,func,ts_f,"log"]))
	testreport_path = os.path.join(TestPath, app.app_name,"report", ".".join([name,func,ts_f,"csv"]))
	testcfg_path = os.path.join(TestPath, app.app_name, module.module_data)
	func_name = testRun.func_name.replace("_", " ")
	cfg = ConfigParser.RawConfigParser()
	cfg.optionxform = str
	cfg.read(testcfg_path)
	arg_list = [JMeterPath, "-n","-t" + testplan_path, "-j" + testlog_path, "-l" + testreport_path]
	arg_list.append("-JTOTAL="+str(module.module_threads))
	arg_list.append("-JLOOP="+str(module.module_loop))
	arg_list.append("-JRAMPUP="+str(module.module_ramp_up))
	arg_list.append("-JTARGET="+module.module_target)
	for (key,value) in cfg.items("common"):
		if key != "functions":
			arg_list.append("-J" + key + "=" +value)
	if cfg.has_section(func_name):
		for (key,value) in cfg.items(func_name):
			arg_list.append("-J" + key + "=" +value)
		
	result = subprocess.call(arg_list)
	if  result == 0:		
		testRun.result = _checkLog(testlog_path)
	else:
		testRun.result = "error"
	testRun.save()
	_removeLock(name,func)
#	except Exception as e:
#		testRun.result = "exception"
#		testRun.message = str(e)
#		testRun.save()
		
	return testRun.result

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
	path = os.path.join(TestPath,"lock",".".join([name,func,"lock"]))
	if (os.path.isfile(path)):
		raise Exception("Only allow one instance running for one function")
	file = open(path,"w")
	file.write(str(os.getpid()))
	file.close()

def _removeLock(name,func):
	path = os.path.join(TestPath,"lock",".".join([name,func,"lock"]))
	if (os.path.isfile(path)):
		os.remove(path)

def _add_item(all_items,name,level,prefix):
	a_item = {}
	a_item["name"] = name
	a_item["level"] = level
	a_item["prefix"] = prefix
	all_items.append(a_item)

def dashboard(request):
	apps= Application.objects.all()
	all_items = []
	for app in apps:
		modules = app.module_set.all()
		aName = app.app_name
		_add_item(all_items,aName,1,aName)
		
		for module in modules:
			scenarios = module.scenario_set.all()
			mName = module.module_name
			_add_item(all_items,mName,2,aName + "-" + mName)
			path = os.path.join(TestPath,aName,module.module_data);
			cfg = ConfigParser.RawConfigParser()
			cfg.optionxform = str
			cfg.read(path)
			functions = cfg.get("common","functions").split(",")
			for function in functions:
				idName = aName + "-" + mName + "-" + function.replace(" ","_")
				name = function			
				_add_item(all_items,name,3,idName )
				for scenario in scenarios:
					name = scenario.scenario_name
					sIDName = idName + "-" + name.replace(" ","_")
					_add_item(all_items,name,4,sIDName)

	context = {'all_items':all_items}
	return render(request, 'performance/dashboard.html', context)
					
	
def detail(request):
	pass