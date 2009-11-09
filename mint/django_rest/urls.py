from django.conf.urls.defaults import *

from mint.django_rest.rbuilder.reporting import imagereports, reportdispatcher, reports, views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^rbuilder/', include('rbuilder.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    url(r'^api/reports/type/$', views.ReportTypeView()),
    url(r'^api/reports/type/(.*?)/descriptor/?$', reportdispatcher.ReportTypeDescriptor()),
    url(r'^api/reports/type/(.*?)/data/(.*?)/?$', reportdispatcher.ReportDispatcher()),
)
