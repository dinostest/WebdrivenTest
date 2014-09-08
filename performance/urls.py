from django.conf.urls import url

from performance import views

urlpatterns= [
	url(r'^$', views.index, name='index'),
	url(r'^dashboard', views.dashboard, name='dashboard'),
	url(r'^loadall', views.loadall, name = 'loadall'),
	url(r'^loadcfg$',views.loadcfg, name='loadcfg'),
	url(r'^loadapps$',views.loadapps, name='loadapps'),
	url(r'^loadstatus/(?P<module>\w+)/(?P<func>\w+)$',views.loadstatus, name='loadstatus'),
	url(r'^loadscenario$',views.loadscenario, name='loadscenario'),
	url(r'^loaddata$',views.loaddata, name='loaddata'),
	url(r'^loadreport',views.loadreport, name='loadreport'),
	url(r'^runtest/$',views.runtest, name='runtest'),
	url(r'^savedata$',views.savedata, name='savedata'),
	url(r'^savecfg$',views.savecfg, name='savecfg'),
	url(r'^report/(?P<func>\w+)', views.report, name='report'),
	url(r'^log/(?P<func>\w+)', views.log, name='loadlog'),
	url(r'^(?P<app_name>\w+)/$', views.detail, name = 'detail'),
]