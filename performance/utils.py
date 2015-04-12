import xml.etree.ElementTree as ET
import os,csv,datetime
import copy,xlsxwriter
from performance.models import *
from performance.config import perfCfg
import ConfigParser,json

def scenario_plan():
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			testplan = module.module_testplan
			planfile = os.path.join(perfCfg.TestPath,app.app_name,testplan)
			for scenario in module.scenario_set.all():
				threshold = False 
				Gotit = False
				newtree = ET.parse(planfile)
				root = newtree.getroot()
				hashTree = root.find(".//ThreadGroup/..")
				threadGroups = []
				items = [item for item in iter(hashTree)]
				for item in items:
					print item.tag
					if (item.tag == 'ThreadGroup'):
						threshold = True
						if (not Gotit and item.get("testname")):
							print "append plan " + item.get("testname")
							threadGroups.append(item)
						else:
							if (item.get("testname")):
								print "remove plan " + item.get("testname")
							hashTree.remove(item)
							
					if (threshold and item.tag == 'hashTree'):
						dataitem = item.find(".//CSVDataSet/stringProp[@name=\"filename\"]")
						if (dataitem is not None):
							datapath = dataitem.text
							if (datapath.find(scenario.scenario_data) > 0):
								print datapath + " : " +scenario.scenario_data
								Gotit = True
								threadGroup = threadGroups[-1]
								threadGroup.set("testname",scenario.scenario_name)
								if (len(threadGroups) > 1):
									for threadGroup in threadGroups[:-1]:
										print "remove " + threadGroup.get("testname")
										hashTree.remove(threadGroup)
							else:
								hashTree.remove(item)
								print "remove hashTree "
						else:
							hashTree.remove(item)
				scenarioPlan = os.path.join(TestPath,app.app_name,"scenario",scenario.scenario_name.replace(" ","_") + "." + module.module_testplan)
				newtree.write(scenarioPlan)

def CreateSamples():
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			scenarios = module.scenario_set.all()
			for scenario in scenarios:
				datafile = scenario.scenario_data
				datapath = os.path.join(perfCfg.TestPath,app.app_name,"data",datafile)
				datas = csv.DictReader(open(datapath,"r"))
				for data in datas:
					sample = Sample(scenario=scenario,sample_name=data['sample'],priority=5)
					sample.save()
					for key in data.keys():
						if (key != 'sample'):
							field = Fields(field_name=key,field_value=data[key],field_type="String",sample=sample)
							field.save()

def ImportDatas():
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			scenarios = module.scenario_set.all()
			for scenario in scenarios:
				datafile = scenario.scenario_data
				datapath = os.path.join(perfCfg.TestPath,app.app_name,"data",datafile)
				data = open(datapath, "r").readlines()
				scenario.scenario_header = data[0].rstrip("\n")
				scenario.save()
				for line in data[1:]:
					sample_name = line.split(",")[0].rstrip("\n")
					sample,created = scenario.sample_set.get_or_create(sample_name=sample_name,is_deleted='N',defaults={'sample_value':"None",'priority':5,'is_deleted':'N','scenario':scenario})
					if (created):
						print sample_name
					sample.sample_value = line.rstrip("\n")
					sample.save()
					
def CreateOtherSample():
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			scenarios = module.scenario_set.all()
			for scenario in scenarios:
				sample = Sample(sample_name="others",is_deleted='Y',priority=5,scenario=scenario,sample_value="None")
				sample.save()

def CreateFuncs():
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			path = os.path.join(perfCfg.TestPath,app.app_name, module.module_data);
			cfg = ConfigParser.RawConfigParser()
			cfg.optionxform = str
			cfg.read(path)
			functions = cfg.get("common","functions")
			for func in functions.split(","):
				setting = {}
				for name,value in cfg.items("common"):
					if name != "functions":
						setting[name] = value
				if cfg.has_section(func):
					for name,value in cfg.items(func):
						setting[name] = value
				function  = Function(func_name=func, func_setting=json.dumps(setting),module=module)
				function.save()

def MoveScenario():
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			f_count = module.function_set.all().count()
			functions = module.function_set.all() 
			function = functions[0]
			for scenario in module.scenario_set.all():
				scenario.function = function
				scenario.save()
			
			for function in functions[1:]:
				for scenario in module.scenario_set.all():
					samples = scenario.sample_set.filter(is_deleted='N')
					scenario.module = None
					scenario.function = function
					scenario.id = None
					scenario.save()
					for sample in samples:
						sample.id = None
						sample.scenario = scenario
						sample.save()
					otherSample = Sample(sample_name="others",is_deleted='Y',priority=5,scenario=scenario,sample_value="None")
					otherSample.save()
def add_line_no():
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			f_count = module.function_set.all().count()
			functions = module.function_set.all() 
			
			for function in functions:
				for scenario in function.scenario_set.all():
					samples = scenario.sample_set.filter(is_deleted='N').order_by("id")
					line_no = 1
					for sample in samples:
						sample.line_no = line_no
						sample.save()
						line_no = line_no + 1

def generate_report(release,runname):
	headers = perfCfg.ReportHeader + ['Tag']
	apps = Application.objects.all()
	f_res=[]
	ot_res=[]
	workbook = xlsxwriter.Workbook("report.xlsx")
	f_format = workbook.add_format()
	f_format.set_bg_color('red')
	ot_format = workbook.add_format()
	ot_format.set_bg_color('orange')
	h_format = workbook.add_format()
	h_format.set_font_color("white")
	h_format.set_font_size(12)
	h_format.set_bold()
	h_format.set_bg_color('blue')
	summary = workbook.add_worksheet("summary")
	summary_format = workbook.add_format({
		'bold': True,
		'border': 6,
		'font_size': 18,
		'align': 'center',
		'valign': 'vcenter',
		'fg_color': '#D7E4BC'
	})
	if (runname) :
		title = " ( Release: " + release.name + " and test run name as " + runname + ")"
	else:
		title = " ( Release: " + release.name + ")"
	title = 'Report is generated at ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + title
	summary.merge_range('A1:M4','SAILIS Performance Test Report',summary_format)
	summary.merge_range('A5:M5', title)
	
	
	failedtests = workbook.add_worksheet("failed tests")
	overtimetests = workbook.add_worksheet("overtime tests")
	alltests = workbook.add_worksheet("alltests")
	line_no = 0
	alltests.write_row(line_no,0,["Function"] + headers,h_format)
	alltests.freeze_panes(1,0)
	res = {}
	res["children"] = []
	for app in apps:
		f_ares = []
		ot_ares = []
		ares = {}
		ares["children"] = []
		modules = app.module_set.all()
		for module in modules:
			f_mres = []
			ot_mres = []
			mres = {}
			mres["children"] = []
			for func in module.function_set.all():
				if (runname):
					testRuns = module.testrun_set.filter(func_name=func.func_name.replace(" ","_")).filter(release=release).filter(name=runname)
				else:
					testRuns = module.testrun_set.filter(func_name=func.func_name.replace(" ","_")).filter(release=release).order_by("-ts_string")
				f_fres = []
				ot_fres = []
				fres = {}
				fres["children"] = []
				if len(testRuns) == 0:
					continue
					
				ts_string = testRuns[0].ts_string
				
				for scenario in func.scenario_set.all():
					f_ssres = []
					ot_ssres = []
					ssres = {}
					ssres["children"] = []
					for sample in scenario.sample_set.filter(is_deleted='N'):
						testreports = sample.testreport_set.filter(ts_string=ts_string)
						f_sres = []
						ot_sres = []
						sres = {}
						sres["tests"] = 0
						sres["failed"] = 0
						sres["overtime"] = 0
						sres["max"] = 0
						sres["average"] = 0
						sres["total"] = 0
						sres["name"] = sample.sample_name
						tags = sample.tags.all()
						tags_name = ",".join([tag.tag_name for tag in tags])
						criteria = 5000
						for tag in tags:
							if tag.criteria < criteria:
								criteria = tag.criteria
						for testreport in testreports:
							line_no = line_no + 1
							tres = {}
							tres["action"] = testreport.sample_name
							tres["response_time"] = testreport.response_time
							tres["message"] = testreport.message
							tres["url"] = testreport.URL
							tres["link"] = '=HYPERLINK("[report.xlsx]alltests!A' + str(line_no + 1) + ":K" + str(line_no + 1) + '","' + testreport.sample_name + '")'
							if testreport.result == 'false':
								f_sres.append(tres)
								alltests.set_row(line_no,None,f_format)
								sres["failed"] = sres["failed"] + 1
							elif testreport.response_time > criteria:
								ot_sres.append(tres)
								alltests.set_row(line_no,None,ot_format)
								sres["overtime"] = sres["overtime"] + 1
							item = testreport.JMeterDict()
							item["Tag"] = tags_name
							sres["tests"] = sres["tests"] + 1
							sres["total"] = sres["total"] + item["Response Time"]
							if item["Response Time"] > sres["max"]:
								sres["max"] = item["Response Time"]
						
							column = 1
							alltests.write(line_no,0,func.func_name)
							for key in headers:
								if key != 'URL':
									alltests.write(line_no,column,item[key])
								else:
									alltests.write(line_no,column,"_"+item[key])
								column = column + 1
						addChild(ssres,sres)
						ssres["name"] = scenario.scenario_name
						if len(f_sres) > 0:
							sitem = {}
							sitem["sample"] = sample.sample_value
							sitem["children"] = f_sres
							f_ssres.append(sitem)
						if len(ot_sres) > 0:
							sitem = {}
							sitem["sample"] = sample.sample_value
							sitem["children"] = ot_sres
							ot_ssres.append(sitem)
					addChild(fres,ssres)
					fres["name"] = func.func_name
					if len(f_ssres) > 0:
						ssitem ={}
						ssitem["name"] = scenario.scenario_name
						ssitem["header"] = scenario.scenario_header
						ssitem["children"] = f_ssres
						f_fres.append(ssitem)
					if len(ot_ssres) > 0:
						ssitem ={}
						ssitem["name"] = scenario.scenario_name
						ssitem["header"] = scenario.scenario_header
						ssitem["children"] = ot_ssres
						ot_fres.append(ssitem)
				addChild(mres,fres)
				mres["name"] = module.module_name
				addNodes(f_mres,f_fres,func.func_name)
				addNodes(ot_mres,ot_fres,func.func_name)
			addChild(ares,mres)
			addNodes(f_ares,f_mres,module.module_name)
			addNodes(ot_ares,ot_mres,module.module_name)
			ares["name"] = app.app_name
		addChild(res,ares)
		addNodes(ot_res,ot_ares,app.app_name)
		addNodes(f_res,f_ares,app.app_name)	
	format = workbook.add_format()
	format.set_text_wrap()
	line_no = 0
	level = 1
	column = 0
	formats = initFormats(workbook)
	addTable(summary,res,formats)
	addChart(workbook, summary,res)
	failedtests.set_column(0,4,12)
	overtimetests.set_column(0,4,12)
	for ares in f_res:
		line_no = write_excel(workbook,failedtests,ares,level,column,line_no,formats,"failed")
	line_no = 0
	for ares in ot_res:
		line_no = write_excel(workbook,overtimetests,ares,level,column,line_no,formats,"overtime")
	workbook.close()	

def addTable(summary,res,formats):
	data = []
	headers = ["name","tests","failed","overtime","max","average"]
	for app in res["children"]:
		line = []
		for item in headers:
			if item == "tests":
				tests = app["tests"] - app["failed"] - app["overtime"]
				line.append(tests)
			else:
				line.append(app[item])
		data.append(line)
	summary.set_column(1,6,20)
	summary.add_table(6,1,6 + len(res), 6,{'data':data,
		'columns':[{'header':'Application',
				  'total_string':'Totals'},
				 {'header':'Passed Tests',
				  'total_function':'sum'},
				 {'header':'Failed Tests',
				  'total_function':'sum'},
				 {'header':'Overtime Tests',
				  'total_function':'sum'},
				 {'header':'Max Response Time',
				 'format':formats["time"]},
				 {'header':'Average Response Time',
				 'format': formats["time"]}],
				 'total_row': 1});

def addChart(workbook,summary,res):
	chart = workbook.add_chart({'type': 'pie'})
	chart.add_series({
		'name' : 'Performance Test Result',
		'categories': ['summary',6,2,6,4],
		'values': ['summary',6+len(res),2,6+len(res),4],
		'data_labels': {'percentage':True}
	})
	chart.set_title({'name' : 'Performance Test Results'})
	
	chart.set_style(10)
	
	summary.insert_chart(6 + len(res) + 2, 3, chart)

				 
def addNodes(parent,children,name):
	if len(children) > 0:
		item= {}
		item["name"] = name
		item["children"] = children
		parent.append(item)
	
def setTag():
	loginTag = Tag.objects.get(tag_name="Login")
	searchTag = Tag.objects.get(tag_name="Search")
	otherTag = Tag.objects.get(tag_name="Other")
	apps = Application.objects.all()
	for app in apps:
		modules = app.module_set.all()
		for module in modules:
			funcs = module.function_set.all()
			for func in funcs:
				scenarios = func.scenario_set.all()
				for scenario in scenarios:
					samples = scenario.sample_set.all()
					for sample in samples:
						sample.tags.clear()
						if sample.sample_name.lower().find("login") >= 0:
							sample.tags.add(loginTag)
						elif sample.sample_name.lower().find("search") >= 0:
							sample.tags.add(searchTag)
						else:
							sample.tags.add(otherTag)
						sample.save()
	
def addChild(parent,child):
	if "tests" in  child.keys() and child["tests"] > 0:
		child["average"] = child["total"]/child["tests"]
		parent["children"].append(child)
		if "total" in parent.keys():
			parent["total"] = parent["total"] + child["total"]
			parent["tests"] = parent["tests"] + child["tests"]
			parent["failed"] = parent["failed"] + child["failed"]
			parent["overtime"] = parent["overtime"] + child["overtime"]
			if child["max"] > parent["max"]:
				parent["max"] = child["max"]
		else:
			parent["total"] = child["total"]
			parent["tests"] = child["tests"]
			parent["failed"] = child["failed"]
			parent["overtime"] = child["overtime"]
			parent["max"] = child["max"]


	
def initFormats(workbook):
	formats = {}
	formats["general"] = workbook.add_format()
	formats["general"].set_text_wrap()

	formats["sample"] = workbook.add_format()
	formats["sample"].set_border()
	formats["sample"].set_align("vcenter")
	formats["sample"].set_text_wrap()
	
	formats["level1"] = workbook.add_format()
	formats["level1"].set_bg_color("lime")
	formats["level1"].set_text_wrap()
	formats["level2"]= workbook.add_format()
	formats["level2"].set_bg_color("#808080")
	formats["level2"].set_text_wrap()
	formats["level3"]= workbook.add_format()
	formats["level3"].set_bg_color("cyan")
	formats["level3"].set_text_wrap()
	formats["level4"]= workbook.add_format()
	formats["level4"].set_bg_color("#FF00FF")
	formats["level4"].set_text_wrap()

	time_format = workbook.add_format({'num_format': "#,###"})
	formats["time"] = time_format
	link_format = workbook.add_format()
	link_format.set_font_color("blue")
	link_format.set_text_wrap()
	link_format.set_underline()
	link_format.set_border()
	link_format.set_border_color("red")

	formats["link"] = link_format

	fail_format = workbook.add_format()
	fail_format.set_border()
	fail_format.set_border_color("red")

	formats["failed"] = fail_format
	return formats
	
	
def write_excel(workbook, worksheet,item,level,column,line_no,formats,type):
	worksheet.set_row(line_no,None,None,{'level': level})


	line_str=""
	if level == 1:
		line_str="Application : " + item["name"]
	elif level == 2:
		line_str="Module : " + item["name"]
	elif level == 3:
		line_str = "Function : " + item["name"]
	elif level == 4:
		line_str = "Scenario : " + item["name"]

	elif level == 5:
		rowLen = len(item["children"])
		for value in item["sample"].split(","):
			if rowLen == 1:
				worksheet.write(line_no,column,value,formats["sample"])
			else:
				worksheet.merge_range(line_no,column,line_no + rowLen -1,column,value,formats["sample"])
			column = column + 1
		for result in item["children"]:
			if type == "failed":
				worksheet.write(line_no,column + 1,result["message"],formats["sample"])
			elif type == "overtime":
				worksheet.write(line_no,column + 1,result["response_time"],formats["sample"])
				
			worksheet.set_row(line_no,None,None,{'level': level})
			worksheet.write(line_no,column,result["link"],formats["link"])
			line_no = line_no + 1			
	
	if level < 5:
		worksheet.write(line_no, column,line_str,formats["level"+str(level)])
		if level == 4:
			line_no = line_no + 1
			worksheet.set_row(line_no,None,None,{'level': level + 1})
			worksheet.write_row(line_no,column + 1,item["header"].split(","),formats["sample"])
			if type == "failed":
				worksheet.write_row(line_no,column + 1 + len(item["header"].split(",")) ,["Step", "Message"],formats["sample"])
			elif type == "overtime":
				worksheet.write_row(line_no,column + 1 + len(item["header"].split(",")) ,["Step", "Response Time"],formats["sample"])
		
		line_no = line_no + 1
		if "children" in item.keys():
			for child in item["children"]:
				if level < 5:
					line_no = write_excel(workbook, worksheet,child,level + 1,column + 1,line_no,formats,type)
				else:
					line_no = write_excel(workbook, worksheet,child,level + 1,column + len(item["sample"].split(",")),line_no,formats,type)
	return line_no		