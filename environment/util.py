from performance.models import *
from environment.models import *
from environment.config import envCfg
from datetime import datetime
from multiprocessing import Process
import os,re,json
import paramiko
import pygal,select,io,time,calendar

def render_to_file(svgObj, filename, **kwargs):
	"""Render the graph, and write it to filename"""
	with io.open(filename, 'w', encoding='utf-8') as f:
		f.write(svgObj.render(is_unicode=True, **kwargs))


def _getServerList(testrun):
	services = {}
	function = testrun.module.function_set.get(func_name=testrun.func_name.replace("_", " "))
	for job in function.job_set.all():
		for jobservice in job.jobservice_set.all():
			hostname = jobservice.service.hostname
			if hostname not in services.keys():
				services[hostname] = []
			if jobservice.service not in services[hostname]:
				services[hostname].append(jobservice.service)
	return services
	
def _getMonitorServerList(testrun):
	services = {}
	function = testrun.module.function_set.get(func_name=testrun.func_name.replace("_", " "))
	for job in function.job_set.all():
		for jobservice in job.jobservice_set.all():
			hostname = jobservice.service.hostname
			if jobservice.service.monitored:
				if hostname not in services.keys():
					services[hostname] = []
				if jobservice.service not in services[hostname]:
					services[hostname].append(jobservice.service)
	return services

def createServiceRun(testrun):
	services = _getServerList(testrun)

	for hostname in services.keys():
		server = Server.objects.get(hostname = hostname)
		if server.type != "Windows" :
			client = paramiko.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect(server.hostname,22,key_filename=envCfg.KeyFile, allow_agent=False)
			if not server.memory:
				if (server.type == "Aix"):					
					stdin, stdout, stderr = client.exec_command("svmon -O unit=MB|grep memory|awk '{print $2}'")
				else:
					stdin, stdout, stderr = client.exec_command("free -m|grep Mem|awk '{print $2}'")
				for line in stdout:
					server.memory = int(float(line.strip("\n").strip()))
				server.save()
			if  not server.cpu:
				if (server.type == "Aix"):					
					stdin, stdout, stderr = client.exec_command("lscfg -vp|grep -ip proc")
				else:
					stdin, stdout, stderr = client.exec_command("lscpu")
				cpuinfo = ""
				for line in stdout:
					cpuinfo = cpuinfo + line
				server.cpu = cpuinfo
				server.save()
		
			for service in services[hostname]:
				serviceRun = ServiceRun(service=service, testrun=testrun)				
				if service.type == "Aix":
					command = 'find ' + service.logfile + ' -ctime 1|wc -l'
				else:
					command = 'find ' + service.logfile + ' -daystart|wc -l'
				stdin, stdout, stderr = client.exec_command(command)
				for line in stdout:
					newCreated = int(line.strip("\n").strip())
				if (newCreated):
					command = 'wc -l ' + service.logfile
					stdin, stdout, stderr = client.exec_command(command)
					for line in stdout:
						line_no = int(line.strip("\n").strip().split(" ")[0])
						serviceRun.startline = line_no
						serviceRun.endline = line_no
						serviceRun.message = ""
				else:
					serviceRun.startline = 0
					serviceRun.endline = 0
					serviceRun.message = ""

				# logfile = os.path.basename(service.logfile)
				# logPath = os.path.join(envCfg.LogPath,service.environment.name,testrun.ts_string)
				# if (not os.path.exists(logPath)):
					# os.makedirs(logPath)
				# logPath = os.path.join(logPath,logfile)
				# sftp = client.open_sftp()
				# sftp.get(service.logfile,logPath)
				serviceRun.save()
			if (server.monitor_set.all().count() > 0):
				for monitor in server.monitor_set.all():
					stdin,stdout,stderr = client.exec_command(monitor.headerscript)
					for line in stdout:
						header = line.strip("\n").strip()
					stdin, stdout, stderr = client.exec_command(monitor.script)
					stdin, stdout, stderr = client.exec_command(monitor.pidscript)
					pid = ""
					for line in stdout:
						m = re.search('(\d+$)',line.strip("\n").strip())
						pid = pid + " " + m.group(1)
					monitorRun = MonitorRun(starttime=datetime.now(), endtime=datetime.now(),header=header,pid = pid, monitor = monitor, testrun = testrun, server= server)
					monitorRun.save()
			client.close()
	if len(services.keys()) > 0: 
		p = Process(target=realtimeMonitor,args=(testrun,))
		p.start()
			
def realtimeMonitor(testrun):
	services = _getMonitorServerList(testrun)
	clients = []
	outputs = []
	from pygal.style import LightStyle

	monitorPath = os.path.join(envCfg.LogPath,"monitor",testrun.ts_string)
	if (not os.path.exists(monitorPath)):
		os.makedirs(monitorPath)
	memsvg = os.path.join(monitorPath,"mem.svg")
	cpusvg = os.path.join(monitorPath,"cpu.svg")
	memseries = {}
	cpuseries = {}
	service_list = []

	for hostname in services.keys():
		server = Server.objects.get(hostname = hostname)
		if server.type != "Windows":
			client = paramiko.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect(server.hostname,22,key_filename=envCfg.KeyFile, allow_agent=False)				
			clients.append(client)
			
			for service in services[hostname]:
				memseries[service.name.replace(" ","_")] = []
				cpuseries[service.name.replace(" ","_")] = []
				service_list.append(service.name)
				command = service.pslocator
				input, output,errors = client.exec_command(command)
				for line in output:
					pid = line.strip("\n").strip()
					
				command = service.monitor_script.format(pid, service.name.replace(" ", "_"))
				
				input, output,errors = client.exec_command(command,get_pty=True)
				outputs.append(output.channel)
	print service_list	
	while _getStatus(testrun):
		rl,wl,xl = select.select(outputs,[],[],0.0)
		if (len(rl) > 0):
			for channel in rl:
				line = channel.recv(1024)
				line.strip("\n").strip()
				data = re.split("\s+",line)
				if len(data) > 3:
					service_name = data[0]
					logtime = datetime.strptime(data[1],"%Y-%m-%d_%H:%M:%S")
					mem = int(re.search("(\d+)",data[3]).group(1))
					cpu = float(data[2])
					memseries[service_name].append((logtime,mem))
					
					cpuseries[service_name].append((logtime,cpu))
					
		memchart = pygal.TimeLine(x_label_rotation=45, height=200,width=800,style=LightStyle,show_minor_y_labels=False)
		cpuchart = pygal.TimeLine(x_label_rotation=45, height=200,width=800,style=LightStyle,show_minor_y_labels=False)		
		for service_name in service_list:
			memchart.add(service_name, memseries[service_name.replace(" ", "_")])
			cpuchart.add(service_name, cpuseries[service_name.replace(" ", "_")])
		memchart.render_to_file(memsvg)
		cpuchart.render_to_file(cpusvg)
		
		time.sleep(2)
	
	for client in clients:
		client.close()
				
def _getStatus(testrun):
	testrun = TestRun.objects.get(id=testrun.id)
	if testrun.result == "running" or testrun.result == "Queued":
		return True
	else:
		jobruns = testrun.jobrun_set.all()
		for jobrun in jobruns:
			if not jobrun.status == "completed":
				return True
	
	return False
		
			
def endServiceRun(testrun):
	services = _getServerList(testrun)
	jobruns = testrun.jobrun_set.all().exclude(status= "started")
	if (jobruns.count() > 0):
		return

	for hostname in services.keys():
		server = Server.objects.get(hostname = hostname)
		if server.type != "Windows" :
			client = paramiko.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect(server.hostname,22,key_filename=envCfg.KeyFile, allow_agent=False)				
				
			for service in services[hostname]:
				serviceRun = ServiceRun.objects.get(service=service, testrun=testrun)
				command = 'wc -l ' + service.logfile
				stdin, stdout, stderr = client.exec_command(command)
				for line in stdout:
					line_no = int(line.strip("\n").strip().split(" ")[0])
					serviceRun.endline = line_no
					serviceRun.message = ""
				logfile = os.path.basename(service.logfile)
				logPath = os.path.join(envCfg.LogPath,service.environment.name,testrun.ts_string)
				if (not os.path.exists(logPath)):
					os.makedirs(logPath)
				logPath = os.path.join(logPath,logfile)
				sftp = client.open_sftp()
				sftp.get(service.logfile,logPath)
				serviceRun.save()
			for monitorrun in testrun.monitorrun_set.filter(monitor__in = server.monitor_set.all()):
				monitorPath = os.path.join(envCfg.LogPath,"monitor",testrun.ts_string)
				if (not os.path.exists(monitorPath)):
					os.makedirs(monitorPath)
				monitorPath = os.path.join(monitorPath,server.hostname + "_vmstat.csv")
				monitorrun.endtime = datetime.now()
				monitorrun.save()
				client.exec_command("kill -9 " + monitorrun.pid)
				sftp.get("vmstat.csv",monitorPath)
				f = open(monitorPath,"r")
				memory = []
				cpu = []
				for line in f.readlines():
					data = re.split("\s+",line)
					logtime = datetime.strptime(data[0],"%Y-%m-%d_%H:%M:%S")
					if server.memory:
						totalmem = server.memory
					if server.type == "Aix":
						memper = float(data[3])/256 * 100/totalmem
						cpuper = int(data[14]) + int(data[15])
					else:
						memper = 100 - float(data[4])/1024 * 100/totalmem
						cpuper = int(data[13]) + int(data[14])
					memory.append((logtime,memper))
				
					
					cpu.append((logtime,cpuper))
				from pygal.style import LightStyle
				chart = pygal.TimeLine(x_label_rotation=45, height=200,width=800,style=LightStyle,show_minor_y_labels=False)
				chart.add("Mem Usage", memory)
				chart.add("CPU Usage", cpu)
				chart.render_to_file(monitorPath.replace(".csv",".svg"))
				f.close()
					
			client.close()
	if (testrun.jobrun_set.all().count() > 0):
		populateTestResult(testrun)
		
def populateTestResult(testrun):
	for serviceRun in testrun.servicerun_set.all():
		service = serviceRun.service
		logPath = os.path.join(envCfg.LogPath,service.environment.name,testrun.ts_string,os.path.basename(service.logfile))
		f = open(logPath,"r")
		startline = serviceRun.startline
		if startline >= serviceRun.endline :
			startline = 0
		line_no = startline
		results = {}
		for line in f.readlines():
			if line_no < startline:
				line_no = line_no + 1
				continue
			else:
				for jobrun in testrun.jobrun_set.all():
					if (line.find(jobrun.value) >= 0):
						jobservices = jobrun.job.jobservice_set.filter(service=service)
						for jobservice in jobservices:
							m = re.search(jobservice.pattern,line)
							if (m):
								jobrunresult = {}
								if (jobrun.value in results.keys()):
									jobrunresult = results[jobrun.value]
								result = {}
								if (jobservice.name in jobrunresult.keys()):
									result = jobrunresult[jobservice.name]
								item = m.groupdict()
								result[item["name"]] = item["value"]
								jobrunresult[jobservice.name] = result
								results[jobrun.value] = jobrunresult
							else:
								continue
					else:
						continue
			line_no = line_no + 1
		#assume test would complete within one nature day
		for transId in results.keys():
			jobrun = testrun.jobrun_set.get(value=transId)
			jobrun.status = "processing"
			jobrun.save()
			jobrun.status = "completed"
			for key in results[transId].keys():
				jobservice = JobService.objects.get(name = key)
				result = results[transId][key]
				processTime = True
				status = "completed"
				if (not jobservice.starttime == "N/A"):				
					if (jobservice.starttime in result.keys()):
						starttime = testrun.ts_string.split("_")[0] + " " + result[jobservice.starttime].replace(",",".")
					else:
						status = "error"
						starttime = "N/A"
						jobrun.status = status
				else:
					processTime = False
					starttime = "N/A"
				if (not jobservice.endtime == "N/A"):
					if (jobservice.endtime in result.keys()):
						endtime = testrun.ts_string.split("_")[0] + " " + result[jobservice.endtime].replace(",",".")
					else:
						status = "error"
						endtime = "N/A"
						jobrun.status = status
				else:
					processTime = False
					endtime = "N/A"
				duration = 0
				if (processTime and status != "error"):
					duration = getMilliSec(starttime,endtime)
				print key + ":" + str(duration)
				jobServiceResult = JobServiceResult(jobrun = jobrun, servicerun=serviceRun,jobservice=jobservice,starttime=starttime,endtime=endtime,processtime = duration,status=status,value=json.dumps(result))
				jobServiceResult.save()
			jobrun.save()
		f.close()
		
def getMilliSec(starttime,endtime):
	stime = datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S.%f")
	etime = datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S.%f")
	delta = etime - stime
	return delta.total_seconds() * 1000