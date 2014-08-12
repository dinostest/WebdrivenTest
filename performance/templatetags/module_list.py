from django.template import Library
from django.template.loader import get_template
from django.template.context import Context
from performance.views import TestPath
import os

register = Library()

@register.inclusion_tag('performance/module_list.html')
def module_list(module):
	app_name = module.application.app_name
	app_path = os.path.join(TestPath, app_name)
	
	
	