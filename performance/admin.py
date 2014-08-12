from django.contrib import admin
from performance.models import Application, Module, Scenario

class ScenarioInline(admin.TabularInline):
	model = Scenario
	extra = 1

class ModuleInline(admin.TabularInline):
	model = Module
	extra = 1



class ApplicationAdmin(admin.ModelAdmin):
	fields = ['app_name', 'app_description']
	inlines = [ModuleInline]
	list_display = ('app_name', 'app_description')

class ModuleAdmin(admin.ModelAdmin):
	fields = ['module_name', 'module_threads', 'module_ramp_up', 'module_loop','module_target','module_testplan'		,'module_data']
	inlines = [ScenarioInline]
	list_display = ('module_name', 'module_threads', 'module_ramp_up', 'module_loop','module_target',			'module_testplan','module_data')
	
	
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Module, ModuleAdmin)

# Register your models here.
