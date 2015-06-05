from django.conf.urls import url

from automation import views

urlpatterns= [
	url(r'^$', views.index, name='autoindex'),
	url(r'^loadapps', views.loadapps, name='loadapps'),
	url(r'^loadcfg', views.loadcfg, name='loadcfg'),
	url(r'^loadscenario', views.loadscenario, name='loadscenario'),
	url(r'^fetchscenario', views.fetchscenario, name='fetchscenario'),
	url(r'^loaddata', views.loaddata, name='loaddata'),
	url(r'^savedata', views.savedata, name='savedata'),
	url(r'^savescenario', views.savescenario, name='savescenario'),
	url(r'^admin', views.admin, name='admin'),
	url(r'^loadtree', views.loadtree, name='loadtree'),
	url(r'^savenode', views.savenode, name='savenode'),
]