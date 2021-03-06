from datetime import datetime, timedelta
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from main import design
from main.models import AccountPlan

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100,
        error_messages={'required': design.this_field_is_required})
    password = forms.CharField(max_length=50,
        widget=forms.widgets.PasswordInput(),
        error_messages={'required': design.this_field_is_required})
    next_url = forms.CharField(max_length=256,
        widget=forms.HiddenInput,
        error_messages={'required': design.this_field_is_required})

class ChangePlanForm(forms.Form):
    plan = forms.ChoiceField(
        choices=[(0, "Free")] + [(plan.id, "{0} - ${1}/mo".format(plan.title, plan.usd_per_month)) for plan in AccountPlan.objects.order_by('usd_per_month')],
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
    agree_to_terms = forms.BooleanField(error_messages={'required': design.must_agree_to_terms})
    plan = forms.ChoiceField(
        choices=[(0, "Free")] + [(plan.id, "{0} - ${1}/mo".format(plan.title, plan.usd_per_month)) for plan in AccountPlan.objects.order_by('usd_per_month')],
        error_messages={'required': design.this_field_is_required})

    def clean_confirm_password(self):
        password1 = self.cleaned_data.get('password', '')
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

class ContactForm(forms.Form):
    from_email = forms.EmailField(label="Your email:", error_messages={'required': design.this_field_is_required})
    message = forms.CharField(max_length=5000, widget=forms.Textarea)

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(max_length=50,
        widget=forms.widgets.PasswordInput(),
        error_messages={'required': design.this_field_is_required})
    new_password = forms.CharField(max_length=50,
        widget=forms.widgets.PasswordInput(),
        error_messages={'required': design.this_field_is_required})
    confirm_password = forms.CharField(max_length=50,
        widget=forms.widgets.PasswordInput(),
        error_messages={'required': design.this_field_is_required})

    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')

        if new_password != confirm_password:
            raise forms.ValidationError(design.passwords_do_not_match)

        return confirm_password

class EmailSubscriptionsForm(forms.Form):
    notifications = forms.BooleanField(required=False)
    newsletter = forms.BooleanField(required=False)

class PasswordResetForm(forms.Form):
    email = forms.EmailField(max_length=80, error_messages={'required': design.this_field_is_required})

class PreferencesForm(forms.Form):
    show_tips = forms.BooleanField(required=False)
