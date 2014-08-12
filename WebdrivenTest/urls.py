from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sailis.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
	url(r'^performance/', include('performance.urls')),
    url(r'^admin/', include(admin.site.urls),{'extra_context' : {'title':'SAILIS Performance Test Management'}}),
)
