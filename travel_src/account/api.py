from tastypie.resources import ModelResource

from account.models import Account


class AccountResource(ModelResource):

	class Meta:
		queryset = Account.objects.filter(imported=True)
		resource_name = "account"
		fields = ['id','email','name','imported','external_id']

		methods = ['get','delete',]