
from django.core.management.base import BaseCommand, CommandError
import os
from account.models import Account
import requests
import json
from datetime import datetime as dt
from django.utils.timezone import utc

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

#		self.__import_new_accounts_from_third_party()

		self.__send_deleted_accounts__()

#		self.__send_new_accounts_to_third_party__()

		return

	def __send_new_accounts_to_third_party__(self):
		accounts = Account.objects.filter(synched=False,imported=False,deleted=False)


		for acc in accounts:
			result,status = self.__send_new_account__(acc)

			if result:
				self.stdout.write(('Successfully synched account "%s"' + os.linesep) % acc)
				acc.synched = True
				acc.save()
			else:
				self.stdout.write(("Synch Failed for %s with %s"+os.linesep) % (acc,status))

		print_seperator()

		self.stdout.write( "done" )

	def __send_deleted_accounts__(self):
		"""
		Query accounts to find all deleted, not imported and synched accounts
		and send them to the Third Party API if they still exists in their database
		"""
		deleted_accounts = Account.admin_objects.filter(deleted=True,delete_synced=False,imported=False,synched=True)

		for acc in deleted_accounts:
			print "Deleted: %s " % acc
			del_acc_email = acc.email
			if del_acc_email in self.users_emails:
				print "Account exists in third party %s " % del_acc_email
				self.__send_deleted_account_to_api__(acc)
		pass

	def __send_deleted_account_to_api__(self,acc):
		account_data = {"email":acc.email}

		r = self.__send_to_api__("delete",data=account_data)

		if r.status_code in [200,201]:
			print "Delete succeeded Text:%s " % r.text
			acc.delete_synced = True
			acc.save()
			return True
		else:
			print "Delete FAILED Text:%s Code:%s" % (r.text,r.status_code)
			pass


	def __get_accounts_from_api__(self):
		"""
		Connects to the Third party and returns the account objects
		as array of dicts
		"""
		print "Downloading accounts from %s with %r" % (external_api,parameters)

		r = self.__send_to_api__("get",is_json=False)

		print r.json,r.json.__class__
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
		accounts = Account.objects.filter(email__in=self.users_emails)

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


	def __create_new_account__(self,email,user_data):
		"""
		We found a new account that does not exist in our database.
		Create a Django User from user email and the associated Account object.
		Password is automatically generated for the user.
		"""
		try:
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
								  imported_date = dt.utcnow().replace(tzinfo=utc)
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

		r = self.__send_to_api__(data=account_data)

		if r.status_code in [200,201]:
			print "{0}Success{0}".format( 10 * "#")
			print "Code:%s Text:%s Json:%s" % (r.status_code,r.text,r.json)
			return True,r.status_code
		else:
			print "{0}~~~Error~~~{0}".format( 10 * "#")
			print "Code:%s Text:%s Json:%s" % (r.status_code,r.text,r.json)
			return False,r.status_code

	def __send_to_api__(self,method="get",data=None,is_json=True,**kwargs):
		if is_json:
			return requests.request(method,external_api,params=parameters,data=json.dumps(data),headers=headers,**kwargs)
		else:
			return requests.request(method,external_api,params=parameters,data=data,**kwargs)

def print_seperator():
	print 30 * "#"