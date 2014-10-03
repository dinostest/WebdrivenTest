
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
from django.db.models import Max,Avg
from performance.models import Application, Module, TestRun,TestReport,Scenario,Sample
from multiprocessing import Process,Queue
from django.contrib.auth.decorators import login_required

from performance.Queues import queues
from config import perfCfg
import os, json, csv, urllib,re
import ConfigParser,shutil,subprocess,time,datetime


#TestPath = "c:\\SAILIS\\"
#JMeterPath = "C:\\apache-jmeter-2.10\\bin\\jmeter.bat"
#JMeterHeader = ['Time Stamp', 'Response Time','Sample Name','Response Code','Response Message','Thread Name','Type','Result','Bytes','URL','Latency']
#ReportHeader = ['Sample Name','Result','Time Stamp', 'Response Time','Response Code','Response Message','Type','URL','Bytes','Latency']


	
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
			path = os.path.join(perfCfg.TestPath,app.app_name, module.module_data);
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
				if (testRun):
					f["report"] = testRun.ts_string
					f["log"] = testRun.ts_string
				else:
					f["report"] = ""
					f["log"] = ""
				f["scenarios"] = []
				for scenario in module.scenario_set.all():
					s = {}
					s['name'] = scenario.scenario_name;
					s['data'] = scenario.scenario_data;
					s["status"] = testRun.result
					s["report"] = testRun.ts_string
					s["level"] = "scenario"
					s["log"] = testRun.ts_string
					try:
						testReports = scenario.testreport_set.filter(func_name=testRun.func_name,ts_string=testRun.ts_string)
					except TestReport.DoesNotExist:
						testReports=None
				
					if(testReports):
						s['responsetime'] = testReports.aggregate(max_duration=Max('response_time'))['max_duration']
						s['avgtime'] = int(testReports.aggregate(avg_duration=Avg('response_time'))['avg_duration'])
						s['total'] = testReports.count()
						s['failed'] = testReports.filter(result='false').count()
						if (s['failed'] == 0):
							s['status'] = 'completed'
						_set_max(f,s['responsetime'],'responsetime')
						_set_max(m,s['responsetime'],'responsetime')
						_set_max(result,s['responsetime'],'responsetime')
						_set_max(res,s['responsetime'],'responsetime')
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
			else:
				return
		avg = int(sum/dict[num_key])
		dict[key] = avg
	
def _set_max(dict, value, key):
	if key in  dict.keys():
		if value > dict[key]:
			dict[key] = value
	else:
		dict[key] = value
def loaddata(request):
	app = request.GET["app"]
	datafile = request.GET["file"]
	scenario = request.GET["scenario"]
	s = Scenario.objects.get(scenario_name=scenario)
	path = os.path.join(perfCfg.TestPath,app,"data",datafile)
	data = csv.DictReader(open(path,"r"))

	result={}
	result["data"] = [_urlDecode(s, l) for l in data]
	_unique_sample_name(result["data"])
#	if '$Priority$' not in data.fieldnames:
#		data.fieldnames.append('$Priority$')
	result["header"] = data.fieldnames
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
#		if (data['Sample Name'].find(">>") > 0):
#			sample = Sample.objects.get(sample_name = data['Sample Name'])
#			data['Priority'] = sample.priority
#		else:
#			data['Priority'] = "N/A"
		if data['URL'] != 'null':
			data_list.append(data)
	
	result={}
	result["data"] = data_list
	result["header"] = perfCfg.ReportHeader
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
	path = os.path.join(perfCfg.TestPath,app, a_module.module_data);
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
	scenario = Scenario.objects.get(scenario_data = datafile)
	path = os.path.join(perfCfg.TestPath,app,"data",datafile)
	backup_path = path + ".bak"
	shutil.copy(path, backup_path)
	data = json.loads(request.body)
	header = data["header"]
	sheetdata = data["data"]
	csv_file = open(path,"w")
	csv_file.write(",".join(header) + "\n");
#	scenario.sample_set.filter(is_deleted='N').update(is_deleted='Y')
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
			data_line = map(lambda x: "" if (x == None) else urllib.quote_plus(str(x)), line[1:])
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
	path = os.path.join(perfCfg.TestPath,app,module.module_data)
	backup_path = path + ".bak"
	shutil.copy(path, backup_path)
	
	cfg = ConfigParser.RawConfigParser()
	cfg.optionxform = str
	cfg.read(path)
	for item in data["cfg"]:
		cfg.set("common",item["Key"],item["Value"])
	cfg_file = open(path, "w");
	cfg.write(cfg_file)
	cfg_file.close()
	result={}
	result["module"]=module.module_name
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
	if ("scenario" in request.GET.keys()):
		scenario = urllib.unquote_plus(request.GET["scenario"])
		
	timestamp = items[0] + " " + items[1].replace("-",":")
	
	#try:
	testRun = TestRun.objects.get(func_name = func, ts_string = ts)
	target = testRun.target
	module = testRun.module
	app = module.application
	report_file = ".".join([module.module_name,func,ts,"csv"])
	report_path = os.path.join(perfCfg.TestPath, app.app_name,"report", report_file)
	result = loadreport(app.app_name, report_file)
	data = []
	for line in result["data"]:
		data_line = []
		for item in perfCfg.ReportHeader:
			data_line.append(line[item])
			
		if (data_line[0].find(scenario) >= 0):
			data.append(data_line)

	context = { 'is_popup': True, 'reportFile': report_file, 'app': app.app_name, 
		'report_name': 'Performance test report for ' + func,'time_stamp':timestamp,'target':target,
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
		testcfg_path = os.path.join(perfCfg.TestPath, app.app_name, module.module_data)
		func_name = testRun.func_name.replace("_", " ")
		cfg = ConfigParser.RawConfigParser()
		cfg.optionxform = str
		cfg.read(testcfg_path)
		arg_list = [perfCfg.JMeterPath, "-n","-t" + testplan_path, "-j" + testlog_path, "-l" + testreport_path]
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
	
	for line in csvFile.readlines():
		data = {}
		items = line.split(",")
		i = 0
		for header in perfCfg.JMeterHeader:
			data[header] = items[i]
			i = i+1
		if (data['Sample Name'].find(">>") > 0):
			scenario_name,sample_name = data['Sample Name'].split(">>")
			scenario_name = scenario_name.strip()
			sample_name = sample_name.strip()
			time_stamp = data['Time Stamp']
			if time_stamp.find(".") > 0:
				time_stamp = time_stamp[:time_stamp.find(".")]
			running_time = datetime.datetime.strptime(time_stamp,"%Y-%m-%d %H:%M:%S")
			testReport = TestReport(func_name=testRun.func_name,sample_name=sample_name,response_time=data['Response Time'],URL=data['URL'],running_time=running_time,response_code = int(data['Response Code']),ts_string=testRun.ts_string,target=testRun.target,result=data['Result'],message=data['Response Message'],scenario=module.scenario_set.get(scenario_name=scenario_name))
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
			scenarios = module.scenario_set.all()
			mName = module.module_name
			_add_item(all_items,mName,2,aName + "-" + mName)
			path = os.path.join(perfCfg.TestPath,aName,module.module_data)
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

	context = {'all_items':all_items, 'title' : "Performance Test Dashboard"}
	return render(request, 'performance/dashboard.html', context)
					
def loadfiletable(request):
	name = request.GET["module"]
	module = Module.objects.get(module_name = name)
	app = module.application
	threads = int(module.module_threads)
	path = os.path.join(perfCfg.TestPath,app.app_name,module.module_data)
	result = {}
	result['name'] = name
	cfg = ConfigParser.RawConfigParser()
	cfg.optionxform = str
	cfg.read(path)
	if (cfg.has_option("common", "filelist")):
		files = cfg.get("common","filelist").split(",")
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
	module = Module.objects.get(module_name = name)
	app = module.application
	threads = int(module.module_threads)
	path = os.path.join(perfCfg.TestPath,app.app_name,module.module_data)
	result = {}
	result['name'] = name
	cfg = ConfigParser.RawConfigParser()
	cfg.optionxform = str
	cfg.read(path)
	files = cfg.get("common","thread-datalist").split(",")
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
	
	
def detail(request):
	pass