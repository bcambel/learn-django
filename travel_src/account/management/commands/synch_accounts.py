
from django.core.management.base import BaseCommand, CommandError
import os
from account.models import Account
import requests
import json
from datetime import datetime as dt
from django.utils.timezone import utc
from django.db.models import Q

external_api = ""
parameters = { "username" : "", "format":"json", "api_key":""  }
headers = {'content-type': 'application/json'}

class Command(BaseCommand):
	"""
		Basic command to synch our database with the external one, and vice versa.
		The External account records are the leading one.
		First get the records from the External API
		Send our new records to the External API.
		Send our DELETED ones to the External API.
		Happy Ending every Hour.
	"""

	args = "<api_url username api_key>"
	help = "Synchronizes accounts with the given API"

	def handle(self,*args,**kwargs):
		api,username,api_key = args

		global external_api,parameters

		external_api = api
		parameters["username"] = username
		parameters["api_key"] = api_key

		print "API:%s U:%s K:%s" % (api,username, api_key[:3] + ((len(api_key)-3) *"*"))

		print "running cron job"
		print_seperator()

		self.__get_accounts__()

		self.__import_new_accounts_from_third_party()

		self.__send_deleted_accounts__()

		self.__send_new_accounts_to_third_party__()

		self.__update_sent_accounts_ids__()


		self.stdout.write( (10*"*") + "done" + os.linesep)

		return

	def __get_new_accounts_from_db__(self,synched=False,imported=False,deleted=False,*args,**kwargs):
		return Account.admin_objects.filter(synched=synched,imported=imported,deleted=deleted,*args,**kwargs)

	def __send_new_accounts_to_third_party__(self):
		accounts = self.__get_new_accounts_from_db__()

		self.send_new_accounts = []

		for acc in accounts:
			result,status = self.__send_new_account__(acc)

			if result:
				self.stdout.write(('Successfully synched account "%s"' + os.linesep) % acc)
				acc.synched = True
				self.send_new_accounts.append(acc.id)
				acc.save()
			else:
				self.stdout.write(("Synch Failed for %s with %s"+os.linesep) % (acc,status))

		print_seperator()



	def __update_sent_accounts_ids__(self):

		print_seperator()

		accounts = Account.admin_objects.filter(Q(id__in=self.send_new_accounts) | Q(external_id=0))


		if len(accounts) > 0:
			print "Update recently inserted Accounts ids with external ids"
			# re-request accounts from the API to update the values of our requests. ( Find their external_ids )
			self.__get_accounts__()
		else:
			print "No new accounts sent. No need to look for external ids"
			return



		for acc in accounts:
			account_lead = self.users_data.get(acc.email)
			if account_lead is None:
				print "Pass %s - %s Not refreshed yet on API" % (acc.email,acc.id)
				# damn records cache probably preventing new records to sent
				continue

			id = self.__extract_account_id__(account_lead.get("resource_uri",None))

			if id is not None:
				acc.external_id = id
				acc.save()

	def __send_deleted_accounts__(self):
		"""
		Query accounts to find all deleted, not imported and synched accounts
		and send them to the Third Party API if they still exists in their database
		"""
		deleted_accounts = Account.admin_objects.filter(deleted=True,delete_synced=False,imported=False,synched=True)
		print "Found %d accounts to be deleted " % len(deleted_accounts)

		for acc in deleted_accounts:
			print "Deleted: %s " % acc
			del_acc_email = acc.email
			if del_acc_email in self.users_emails and acc.external_id is not 0:
				print "Account exists in third party %s " % del_acc_email
				self.__send_deleted_account_to_api__(acc)
			else:
				print "Account does not exist in the API anymore or external id(%s) is not SET.." % acc.external_id


	def __send_deleted_account_to_api__(self,acc):
		account_data = {"email":acc.email,"tr_referral":"BahadirFeed","ip_address":"127.0.0.1"}

		r = self.__send_to_api__("delete",data=account_data,url=external_api+("%d/"%acc.external_id))

		if r.status_code in [200,201,204]:
			print "Delete succeeded Text:%s " % r.text
			acc.delete_synced = True
			acc.save()
			return True
		else:
			print "Delete FAILED  Code:%s Text:%s" % (r.text,r.status_code)
			pass


	def __get_accounts_from_api__(self):
		"""
		Connects to the Third party and returns the account objects
		as array of dicts
		"""
		print "Downloading accounts from %s with %r" % (external_api,parameters)

		r = self.__send_to_api__("get",is_json=False)

#		print r.json,r.json.__class__
		print_seperator()
		result = r.json

		print "Found %d results:" % result["meta"]["total_count"]

		return result['objects']


	def __get_accounts__(self):
		"""
		Create a hash dict of third party accounts from email addresses
		and store the account values as instance variable
		"""
		api_accounts = self.__get_accounts_from_api__()

		self.users_emails = []
		self.users_data = {} # store user records with email hash.

		for user in api_accounts:
			user_email = user["email"]
			print "User: %s Name:%s-%s" % (user_email,user["first_name"],user["last_name"])

			self.users_emails.append(user_email)
			self.users_data[user_email] = user

		print "New 3rd Party Users:%r " % self.users_emails

	def __import_new_accounts_from_third_party(self):
		"""
		Query our database to find the diff of the accounts
		and send to the third party API
		"""
		accounts = Account.admin_objects.filter(email__in=self.users_emails)

		print_seperator()

		found_users = set([acc.email for acc in accounts])

		migrating_users = list(set(self.users_emails) - found_users) # diff already existing accounts

		print "Must migrate %r" % migrating_users

		print_seperator()

		for mig_user_email in migrating_users:
			mig_user = self.users_data.get(mig_user_email,None)
			if mig_user is None:
				print "Somehow we don't have data for this user"
				continue

			print "Create User %r " % mig_user
			self.__create_new_account__(mig_user_email,mig_user)


	def __extract_account_id__(self,resource_uri):
		"""
		since we don't know the ID of the account, we manually extract
		it from the resource uri parameter of the account!
		"""
		id = resource_uri.split('/')[-2]

		return int(id)

	def __create_new_account__(self,email,user_data):
		"""
		We found a new account that does not exist in our database.
		Create a Django User from user email and the associated Account object.
		Password is automatically generated for the user.
		"""
		try:
			id = self.__extract_account_id__(user_data["resource_uri"])

			new_user = Account.create_user(email,email,
										   user_data["first_name"],
										   user_data["last_name"],
										   generate_password=True
			)


			new_account = Account(ip_address=user_data[u'tr_ip_address'],
								  email=email,
								  imported=True,
								  synched=False,
								  name = "%s %s" % (user_data["first_name"],user_data["last_name"]),
								  user = new_user,
								  imported_date = dt.utcnow().replace(tzinfo=utc),
								  external_id = id
			)


			new_account.save()
			return True
		except Exception,e :
			print "Exception %s" % e
			return False

	def __send_new_account__(self,acc):
		post_data = {
			"email" : acc.email,
			"tr_referral":"BahadirFeed",
			"mailing_lists":1,
			"ip_address" : acc.ip_address,
		}

		return self.__send_new_account_to_api__(post_data)

	def __send_new_account_to_api__(self,account_data):

		r = self.__send_to_api__(method="post",data=account_data)

		if r.status_code in [200,201]:
			print "{0}Success{0}".format( 10 * "#")
			print "Code:%s Text:%s Json:%s" % (r.status_code,r.text,r.json)
			return True,r.status_code
		else:
			print "{0}~~~Error~~~{0}".format( 10 * "#")
			print "Code:%s Text:%s Json:%s" % (r.status_code,r.text,r.json)
			return False,r.status_code

	def __send_to_api__(self,method="get",data=None,is_json=True,url=None,**kwargs):
		if url is None:
			url = external_api

		parameters["_ts"] = dt.utcnow().strftime("%s")


		if is_json:
			return requests.request(method,url,params=parameters,data=json.dumps(data),headers=headers,**kwargs)
		else:
			return requests.request(method,url,params=parameters,data=data,**kwargs)

def print_seperator():
	print 30 * "#"