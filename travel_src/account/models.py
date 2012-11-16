from django.db import models
from django.db.models.signals import pre_delete
from django.contrib import admin
from django.contrib.auth.models import User
from datetime import datetime as dt
import os
import string
import random

class AccountManager(models.Manager):
	def get_query_set(self,*args,**kwargs):
		return super(AccountManager, self).get_query_set().filter(deleted=False)

class AdminAccountManager(models.Manager):
	pass

def random_password(size=20, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))


class Account(models.Model):

	user = models.OneToOneField(User)

	email = models.CharField(max_length=200,unique=True)

	name = models.CharField(max_length=200)

	ip_address = models.IPAddressField(blank=True)

	synched = models.BooleanField(blank=False,default=False)

	imported = models.BooleanField(blank=False,default=False)
	imported_date = models.DateTimeField(null=True,blank=True)

	external_id = models.IntegerField(blank=True,null=True,default=0 )

#	active = models.BooleanField(blank=False,default=True)

	# First soft delete, then send to api, and schedule for actual delete.
	deleted = models.BooleanField(blank=False,default=False,editable=False)
	delete_synced = models.BooleanField(blank=False,default=False,editable=False)

	# to exclude our soft deletes, use the AccountManager query set
	objects = AccountManager()

	# sometimes we need to bypass default filters.
	# this dude handles that!
	admin_objects = AdminAccountManager()

	def __unicode__(self):
		return u"%s - %s " % (self.name,self.email)

	def delete(self,*args,**kwargs):
		print "Running soft delete on %s" % self
		self.deleted = True
		self.save()

	@classmethod
	def create_user(cls,username,email,first_name='',last_name='',password=None,generate_password=False):

		if len(username) > 30:
			username = username[:30]

		user = User(username=username,email=email,first_name=first_name,last_name=last_name)

		if generate_password:
			user.set_password(random_password())
#		elif (not generate_password) and password is None:
#			raise ValueError("Password is missing.Either set generate_password True to create a random one or supply a password")
#
		user.set_password(password)

		try:
			user.save()
		except User.DoesNotExist, dne:
			raise dne

		return user




def soft_delete_account(sender,instance,**kwargs):
	"""
	On bulk deletes, account's delete method is not called. Handle the pre_delete signal
	to actually soft delete the object
	"""
	account = Account.objects.get(instance.id)
	account.delete()
	return False



pre_delete.connect(soft_delete_account,User)



