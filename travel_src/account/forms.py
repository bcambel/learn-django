from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm

from account.models import Account

class RegistrationForm(ModelForm):
	username = forms.CharField(label=(u"User Name"))
	email 	= forms.EmailField(label=(u"Email Address"))
	password = forms.CharField(label=(u"Password"))#,widget=forms.PasswordInputWidget(render_value=False))
	
	class Meta:
		model = Account
		exclude = ('user',)

	def clean_username(self):
		username = self.cleaned_data["username"]

		try:
			User.objects.get(username=username)
		except User.DoesNotExist:
			return username
		raise forms.ValidationError("That username is already taken..")


	def clean_password(self):
		password = self.cleaned_data["password"]

#class LoginForm(ModelForm):
#	email 	= forms.EmailField(label=(u"Email Address"))
#	password = forms.CharField(label=(u"Password"))#,widget=forms.PasswordInputWidget(render_value=False))
#
#	class Meta:
#		model = User



	
