from django.contrib import admin
from environment.models import *

class ServiceInline(admin.TabularInline):
	model = Service
	extra = 1
	
class JobServiceInline(admin.TabularInline):
	model = JobService
	extra = 1

class EnvironmentAdmin(admin.ModelAdmin):
	fields = ['name', 'description','portal','setting']
	inlines = [ServiceInline]
	list_display = ('name', 'description','portal','setting')
	
class ServerAdmin(admin.ModelAdmin):
	fields = ['hostname','type']
	
class MonitorAdmin(admin.ModelAdmin):
	fields = ['name','headerscript','pidscript','script','server']

class ServiceAdmin(admin.ModelAdmin):
	fields = ['name', 'description', 'hostname', 'port','url','logfile','server','monitored','pslocator','monitor_script']
	list_display = ('name', 'description', 'hostname', 'port','url','logfile','server','monitored','pslocator','monitor_script')

class JobAdmin(admin.ModelAdmin):
	fields = ['name', 'description','pattern','function']
	inlines = [JobServiceInline]
	list_display = ('name', 'description','pattern','function')

class JobServiceAdmin(admin.ModelAdmin):
	fields = ['name', 'description','sequence','service','job']
	
	

	
admin.site.register(Environment, EnvironmentAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Job,JobAdmin)
admin.site.register(JobService,JobServiceAdmin)
admin.site.register(Server,ServerAdmin)
admin.site.register(Monitor,MonitorAdmin)

# Register your models here.
