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
import os, json, csv, urllib,re,socket
from environment.tasktimer import KeepLiveThread,lock
from django.views.decorators.csrf import csrf_exempt
from environment.models import HubCfg

registry = {}
#thread = KeepLiveThread(registry)
#thread.start()

def hub(request):
#simulate the hub server response to node server with default value
	server = {}
	server["success"]=True
	server["port"] = request.META['SERVER_PORT']
	server["host"] = socket.gethostname()
	server["servlets"] = []
	server["cleanUpCycle"] = 5000
	server["browserTimeout"] = 0
	server["newSessionWaitTimeout"] = -1
	server["capabilityMatcher"] = "org.openqa.grid.internal.utils.DefaultCapabilityMatcher"
	server["prioritizer"] = None
	server["throwOnCapabilityNotPresent"]=True
	server["nodePolling"] = 5000
	server["maxSession"] = 5
	server["role"] = "hub"
	server["jettyMaxThreads"] = -1
	server["timeout"] = 300000
	return HttpResponse(json.dumps(server), content_type="application/json")
	
@csrf_exempt
def register(request):
	data = json.loads(request.body)
	id = data["configuration"]["remoteHost"]
	duration = data["configuration"]["registerCycle"]
	lock.acquire()
	registry[id] = Machine(duration,data["configuration"])
	lock.release()
	return HttpResponse(json.dumps("ok"), content_type="application/json")


def proxy(request):
	id = request.GET["id"]
	data = {}
	if id in registry.keys():
		machine = registry[id]
		if machine.aLive:
			data["success"] = True
			data["msg"] = "proxy found !"
			data["request"] = machine.configuration
			lock.acquire()
			machine.duration = machine.configuration["registerCycle"] / 1000 * 3
			lock.release()
			return HttpResponse(json.dumps(data), content_type="application/json")
	
	data["success"] = False
	data["msg"] = "Cannot find proxy with ID =" + id + " in the registry."
	return HttpResponse(json.dumps(data), content_type="application/json")

class Machine(object):
	def __init__(self,duration,configuration):
		self.duration = duration / 1000 * 3
		self.configuration = configuration
		self.aLive = True
		
	def reduce(self):
		if self.duration == 0:
			self.aLive = False
		else:
			self.duration = self.duration - 1
			print str(self.duration)