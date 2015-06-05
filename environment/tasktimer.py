from threading import Thread,Lock
from time import sleep

isStopped = False
lock=Lock()
class KeepLiveThread(Thread):
	def __init__(self,registry):
		self.registry = registry
		super(KeepLiveThread,self).__init__()
		
	def run(self):
		while not isStopped:
			sleep(1)
			lock.acquire()
			for key in self.registry.keys():
				self.registry[key].reduce()
			lock.release()
		return 