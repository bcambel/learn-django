from haystack.query import SearchQuerySet
from tastypie.resources import ModelResource
from tastypie.utils import trailing_slash
from django.conf.urls.defaults import *
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.models import ApiKey
from account.models import Account
import sys

class AccountResource(ModelResource):

	class Meta:
		queryset = Account.objects.filter(imported=True)
		resource_name = "account"
		fields = ['id','email','name','imported','external_id']

		methods = ['get','delete','post']


		#Once the record is created send back the data to the user
		always_return_data = True

		authentication = ApiKeyAuthentication()
		authorization = DjangoAuthorization()

	def override_urls(self):
		return [
			url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
			]


	def obj_create(self, bundle, request=None, **kwargs):

		bundle.obj = self._meta.object_class()
#		raise ValueError(bundle.obj)
		email = None
		str = []

		# well during debugging kwargs seems to be empty somehow!
		# so probably the following for block is totally unnecessary
		# I guess full_hydrate does the magic
		for key, value in kwargs.items():

			str.append("%s = %s" % (key,value))
			print >>sys.stderr,("%s = %s" % (key,value))

			setattr(bundle.obj, key, value)



		bundle = self.full_hydrate(bundle)

		email = bundle.obj.email
		user = Account.create_user(username=email,email=email,generate_password=True)
		bundle.obj.user = user
		bundle.obj.ip_address = "127.0.0.1"


		# Save FKs just in case.
		self.save_related(bundle)

		obj = None

		bundle.obj.save()
			# Now pick up the M2M bits.
		m2m_bundle = self.hydrate_m2m(bundle)
		self.save_m2m(m2m_bundle)

		return bundle

	def get_search(self, request, **kwargs):
		self.method_check(request, allowed=['get'])
		self.is_authenticated(request)
		self.throttle_check(request)

		# Do the query.
		sqs = SearchQuerySet().models(Account).load_all().auto_query(request.GET.get('q', ''))
		paginator = Paginator(sqs, 20)

		try:
			page = paginator.page(int(request.GET.get('page', 1)))
		except InvalidPage:
			raise Http404("Sorry, no results on that page.")

		objects = []

		for result in page.object_list:
			bundle = self.build_bundle(obj=result.object, request=request)
			bundle = self.full_dehydrate(bundle)
			objects.append(bundle)

		object_list = {
			'objects': objects,
			}

		self.log_throttled_access(request)
		return self.create_response(request, object_list)




def generate():
	api_key = ApiKey.objects.get_or_create(user=someuser)
	api_key.key = api_key.generate_key()
	api_key.save()
