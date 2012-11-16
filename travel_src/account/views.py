# Create your views here.
from django.http import HttpResponseRedirect,HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from account.models import Account
import logging
import json
from account.forms import RegistrationForm


logger = logging.getLogger(__name__)

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
			password =form.cleaned_data["password"]
			logger.info( "Password is %s" % password )

			user = Account.create_user(
				email=form.cleaned_data["email"],
				username=form.cleaned_data["username"],
				password= password,
				generate_password=False
			)

			acc = Account(user=user)
			acc.email = form.cleaned_data["email"]
			acc.name = form.cleaned_data["name"]
			acc.synched = False
			acc.ip_address = get_client_ip(request)
			acc.save()

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