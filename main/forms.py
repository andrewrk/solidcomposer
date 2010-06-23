from django import forms

from main.models import *
from main import design
from django.conf import settings

from datetime import datetime, timedelta
import string

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100,
        error_messages={'required': design.this_field_is_required})
    password = forms.CharField(max_length=50,
        widget=forms.widgets.PasswordInput(),
        error_messages={'required': design.this_field_is_required})
    next_url = forms.CharField(max_length=256,
        widget=forms.HiddenInput,
        error_messages={'required': design.this_field_is_required})

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30,
        error_messages={'required': design.this_field_is_required})
    artist_name = forms.CharField(max_length=80,
        error_messages={'required': design.this_field_is_required},
        label=design.label_artist_name)
    email = forms.EmailField(max_length=80,
        error_messages={'required': design.this_field_is_required})
    password = forms.CharField(max_length=50,
        widget=forms.widgets.PasswordInput(),
        error_messages={'required': design.this_field_is_required})
    confirm_password = forms.CharField(max_length=50,
        widget=forms.widgets.PasswordInput(),
        error_messages={'required': design.this_field_is_required})
    
    def clean_confirm_password(self):
        password1 = self.cleaned_data['password']
        password2 = self.cleaned_data['confirm_password']
        if password1 != password2:
            raise forms.ValidationError(design.passwords_do_not_match)

        return password2

    def clean_username(self):
        username = self.cleaned_data['username']

        disallowed_chars = settings.URL_DISALLOWED_CHARS
        for c in username:
            if c in disallowed_chars:
                raise forms.ValidationError(design.invalid_characters_in_user_name % disallowed_chars)

        old_users = User.objects.filter(username=username)
        if old_users.count() > 0:
            # if the account is registered but not activated some time, delete
            # the old account
            old_user = old_users[0]
            expire_date = old_user.date_joined + timedelta(days=settings.ACTIVATION_EXPIRE_DAYS)
            now = datetime.now()
            if now > expire_date:
                old_user.delete()
            else:
                raise forms.ValidationError(design.user_x_already_exists % username)

        return username
   
    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError(design.email_already_exists)

        return email
