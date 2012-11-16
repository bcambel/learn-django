import datetime
from haystack import indexes
from haystack.indexes import *
from haystack import site

from account.models import Account

class AccountIndex(indexes.SearchIndex):
	text = indexes.CharField(document=True, use_template=True)

	def prepare(self,obj):
		self.prepared_data = super(AccountIndex,self).prepare(obj)
		self.prepared_data["text"] = obj.email

site.register(Account,AccountIndex)