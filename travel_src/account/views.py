# Create your views here.
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login

from account.models import Account
import logging
import json
from account.forms import RegistrationForm


logger = logging.getLogger(__name__)
session_account_id_key = "account_id"

def get_client_ip(request):
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0]
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip

def account_registration(request):
#	if request.user.is_authenticated():
#		return HttpResponseRedirect("/profile/")

	if request.method == "POST":
		form = RegistrationForm(request.POST)


		if form.is_valid():
			password = form.cleaned_data["password"]
			logger.info( "Password is %s" % password )

			username = form.cleaned_data["email"]

			if len(username)>30:
				username = username[:30]

			user,success = Account.create_user(
				email=form.cleaned_data["email"],
				username= username,
				password= password,
				generate_password=False
			)

			acc = Account(user=user)
			acc.email = form.cleaned_data["email"]
			acc.name = form.cleaned_data["name"]
			acc.synched = False
			acc.ip_address = get_client_ip(request)
			acc.save()

			request.session[session_account_id_key] = acc.id

			return HttpResponseRedirect("/profile/")
		else:

			response_data = {
				"success":False,
				"errors": [(k, v[0]) for k, v in form.errors.items()]
			}

			return HttpResponse(json.dumps(response_data),mimetype="application/json")
#			return render_to_response("register.html",{"form":form},context_instance=RequestContext(request))

	else:
		"""user not submit"""
		form = RegistrationForm
		context = {"form":form}
		return render_to_response("register.html",context,context_instance=RequestContext(request))

def login_view(request):
	if request.method == "GET":
		context = {}
		return render_to_response("login.html",context,context_instance=RequestContext(request))
	elif request.method == "POST":
#		form = LoginForm(request.POST)
		result = {'success':False}

		password = request.POST["password"]
		email =request.POST["email"]

		def account_not_exist_email_password_wrong():
			result['reason'] = "Email address or password is wrong."
			print "Your username and password were incorrect."

		if password is None or len(password) <= 0:
			result['reason'] = "Please type in your password"
		elif email is None or len(email) <= 0:
			result['reason'] = "Please type in your email"
		else:
			account = None
			try:
				account = Account.admin_objects.get(email=email)
			except Account.DoesNotExist:
				account_not_exist_email_password_wrong()

			if account is not None:
				user = authenticate(username=email, password=password)
				if user is not None:
					if user.is_active:

		#					login(request,user)
						request.session[session_account_id_key] = account.id
						result['success'] = True
						print "You provided a correct username and password!"
					else:
						result['reason'] = "Account disabled"
						print "Your account has been disabled!"
				else:
					account_not_exist_email_password_wrong()
			else:
				account_not_exist_email_password_wrong()

		return HttpResponse(json.dumps(result),mimetype="application/json")



def profile_view(request):
	user_id = request.session.get(session_account_id_key,None)

	if user_id is None:
		return HttpResponseRedirect("/login/")

	acc = Account.objects.get(id=user_id)

	context = {
		"acc":acc
	}
	return render_to_response("profile.html",context,context_instance=RequestContext(request))

def home_view(request):
	return render_to_response("home.html",{},context_instance=RequestContext(request))