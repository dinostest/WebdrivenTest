from django.contrib import admin
from automation.models import *

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
	fields = ['name', 'description']
	inlines = [ModuleInline]
	list_display = ('name', 'description')

class ModuleAdmin(admin.ModelAdmin):
	fields = ['name', 'description']
	inlines = [FunctionInline]
	list_display = ('name', 'description')

class FunctionAdmin(admin.ModelAdmin):
	fields = ['name', 'description']
	inlines = [ScenarioInline]
	list_display = ('name', 'description')



class TagAdmin(admin.ModelAdmin):
	fields = ['tag_name', 'tag_description']

class MachineAdmin(admin.ModelAdmin):
	fields = ['label', 'hostname']

	

	
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Module, ModuleAdmin)
admin.site.register(Tag,TagAdmin)
admin.site.register(TestMachine,MachineAdmin)
admin.site.register(Function,FunctionAdmin)


# Register your models here.

