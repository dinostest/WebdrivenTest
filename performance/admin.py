from django.contrib import admin
from performance.models import Application, Module, Scenario,Function,Tag

class ScenarioInline(admin.TabularInline):
	model = Scenario
	extra = 1

class ModuleInline(admin.TabularInline):
	model = Module
	extra = 1

class FunctionInline(admin.TabularInline):
	model = Function
	extra = 1


class ApplicationAdmin(admin.ModelAdmin):
	fields = ['app_name', 'app_description']
	inlines = [ModuleInline]
	list_display = ('app_name', 'app_description')

class ModuleAdmin(admin.ModelAdmin):
	fields = ['module_name', 'module_threads', 'module_ramp_up', 'module_loop','module_target','module_testplan'		,'module_data']
	inlines = [ScenarioInline,FunctionInline]
	list_display = ('module_name', 'module_threads', 'module_ramp_up', 'module_loop','module_target',			'module_testplan','module_data')

class TagAdmin(admin.ModelAdmin):
	fields = ['tag_name', 'tag_description']
	

	
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Tag,TagAdmin)

# Register your models here.
