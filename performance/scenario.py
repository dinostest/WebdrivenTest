import xml.etree.ElementTree as ET
import os,csv
import copy
from performance.models import Application,Module,Scenario,Sample,Fields,Function
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