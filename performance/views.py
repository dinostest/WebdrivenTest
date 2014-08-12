from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Max
from performance.models import Application, Module, TestRun
from multiprocessing import Process
import os, json, csv
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

def loaddata(request):
	app = request.GET["app"]
	datafile = request.GET["file"]
	path = os.path.join(TestPath,app,"data",datafile)
	data = csv.DictReader(open(path,"r"))
	result={}
	result["data"] = [l for l in data]
	result["header"] = data.fieldnames
	return HttpResponse(json.dumps(result), content_type="application/json")
	
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
	is_popup = True
	context = {'app':app,'data_file':datafile, 'is_popup': is_popup}
	return render(request, 'performance/data.html', context)
	
def loadcfg(request):
	app = request.GET["app"]
	module = request.GET["test"]
	a_module = Module.objects.get(module_name=module);
	path = os.path.join(TestPath,app, app + "-" + module +".cfg");
	cfg = ConfigParser.RawConfigParser()
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
			line = map(lambda x: "" if (x == None) else x, line)				
			csv_file.write(",".join(line) + "\n")
	
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
		testRuns = TestRun.objects.filter(func_name=func).order_by('timestamp')
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
	#_runtest(module,func,ts_f);
	p = Process(target=_runtest, args=(module,func,ts_f))
	p.start()
	#p.join()
	result={}
	result["module"] = data["module"]
	result["func"]= data["func"]
	result["ts_f"]=ts_f
	return HttpResponse(json.dumps(result), content_type="application/json")

	
def _runtest(name, func, ts_f):
	module = Module.objects.get(module_name=name)
	_createLock(name,func)
	testRun = TestRun(module=module,func_name=func,ts_string=ts_f)
	testRun.save()
	try:
		app = module.application
		testplan_path = os.path.join(TestPath, app.app_name,module.module_testplan)
		testlog_path = os.path.join(TestPath, app.app_name,"log", ".".join([name,func,ts_f,"log"]))
		testreport_path = os.path.join(TestPath, app.app_name,"report", ".".join([name,func,ts_f,"csv"]))
		testcfg_path = os.path.join(TestPath, app.app_name, module.module_data)
		func_name = func.replace("_", " ")
		cfg = ConfigParser.RawConfigParser()
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
	except Exception as e:
		testRun.result = "exception"
		testRun.message = str(e)
		testRun.save()
		
	return testRun.result

def _checkLog(log_file):
	logfile = open(log_file, "r")
	data = logfile.readlines()
	logfile.close()
	failed  = filter(lambda x: "failed" in x,data)
	error =  filter(lambda x:"error" in x,data)
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
		
def detail(request):
	pass