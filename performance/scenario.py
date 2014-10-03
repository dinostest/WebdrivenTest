import xml.etree.ElementTree as ET
import os,csv
import copy
from performance.models import Application,Module,Scenario,Sample,Fields
from performance.config import perfCfg

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
	