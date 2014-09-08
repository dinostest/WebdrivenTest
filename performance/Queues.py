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

from multiprocessing import Process,Queue



class Queues(object):
	def __init__(self):
		self.queueList = []
		
	
	def names(self):
		for item in self.queueList:
			yield item.name
	
	def get(self,queueName):
		for item in self.queueList:
			if queueName == item.name:
				return item
	
	def put(self, queueName, item):
		name = queueName.strip().lower()
		if not( name in self.names()):
			queueItem = QueueItem(name)
			self.queueList.append(queueItem)
		else:
			queueItem = self.get(name)
		queueItem.put(item)

class QueueItem(object):
	def __init__(self,name):
		super(QueueItem, self).__init__()
		self.name = name.strip().lower()
		self.queue = Queue()
		self.started = False
		self.process = None
		
		
	
	def put(self, item):
		self.queue.put(item)
		if not(self.process):
			self.process = Process(target=_worker, args=(self.queue,))
		if not(self.process.is_alive()):
			if (self.started):
				self.process = Process(target=_worker, args=(self.queue,))
			self.process.start()
			self.started = True
			
def _worker(queue):
	from performance.views import runTest
	while not queue.empty():
		testRun = queue.get()
		runTest(testRun)

queues = Queues()