from django.conf.urls import url

from environment import views

urlpatterns= [
	url(r'^api/hub$', views.hub, name='hub'),
	url(r'^register$', views.register, name='register'),
	url(r'^api/proxy$', views.proxy, name='proxy')
]