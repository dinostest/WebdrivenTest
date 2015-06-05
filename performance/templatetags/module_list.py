from django.template import Library
from django.template.loader import get_template
from django.template.context import Context
from json import dumps
import os,urllib

register = Library()

def dateformat(ts_string):
	date, time = ts_string.split("_")
	return date + " " + time.replace("-",":") + ":00"

def sixitems(number):
	if number % 6 == 0:
		return True
	else:
		return False
		
def jsondata(value):
	return dumps(value)

def encodeurl(urlstr):
	return urllib.quote_plus(urlstr.replace("_"," "))
	
def getItem(dictItem, name):
	return dictItem[name]
	
def getHeader(itemName):
	if itemName.find("Time") >=0 :
		return "dinos_text"
	else :
		return "dinos_number"
	
def getDictKeys(dict, name):
	return dict[name].keys()
	
register.filter('dateformat', dateformat)	
register.filter('sixitems', sixitems)	
register.filter('encodeurl', encodeurl)	
register.filter('jsondata', jsondata)
register.filter('getItem', getItem)
register.filter('getDictKeys',getDictKeys)
register.filter('getHeader',getHeader)