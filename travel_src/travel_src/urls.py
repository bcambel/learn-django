from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from account.views import account_registration

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
	(r"^register/$","account.views.account_registration"),
	(r'^search/', include('haystack.urls')),
)

urlpatterns += staticfiles_urlpatterns()