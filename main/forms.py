from django import forms

from opensourcemusic.main.models import *

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=50, widget=forms.widgets.PasswordInput())
    next_url = forms.CharField(max_length=256, widget=forms.HiddenInput)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=24)
    email = forms.EmailField(max_length=32)
    password = forms.CharField(max_length=50, widget=forms.widgets.PasswordInput())
    confirm_password = forms.CharField(max_length=50, widget=forms.widgets.PasswordInput())
    
    def clean_confirm_password(self):
        password1 = self.cleaned_data['password']
        password2 = self.cleaned_data['confirm_password']
        if password1 != password2:
            raise forms.ValidationError("Your passwords do not match.")

        return password2

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(username=username).count() > 0:
            raise forms.ValidationError("The user '%s' already exists." % username)

        return username
   
    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError("This email address already exists.")

        return email
