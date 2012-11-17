from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from account.api import AccountResource
from account.views import account_registration
from tastypie.api import Api

admin.autodiscover()

v1_api = Api(api_name="v1")
v1_api.register(AccountResource())


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
	(r"^register/?$","account.views.account_registration"),
	(r"^profile/?$","account.views.profile_view"),
	(r"^login/?$","account.views.login_view"),
	(r"^/?$","account.views.home_view"),
	(r'^search/', include('haystack.urls')),
	(r'^api/', include(v1_api.urls)),
)

urlpatterns += staticfiles_urlpatterns()