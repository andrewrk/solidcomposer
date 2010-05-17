from django import forms

from opensourcemusic.competitions.models import *

from datetime import datetime, timedelta

HOURS, DAYS, WEEKS = range(3)

class SubmitEntryForm(forms.Form):
    title = forms.CharField(max_length=100)
    comments = forms.CharField(max_length=1000, required=False, widget=forms.Textarea)
    file_mp3 = forms.FileField()
    file_source = forms.FileField(required=False)

    def clean_file_mp3(self):
        filename = self.cleaned_data['file_mp3']

        if filename[:3].lower() != 'mp3':
            raise forms.ValidationError("Uploaded file must be an mp3.")

        return filename

class CreateCompetitionForm(forms.Form):
    TIME_QUANTIFIERS = (
        (HOURS, "hours"),
        (DAYS, "days"),
        (WEEKS, "weeks"),
    )

    title = forms.CharField(max_length=100)

    have_theme = forms.BooleanField(required=False)
    preview_theme = forms.BooleanField(required=False)
    theme = forms.CharField(max_length=20000, required=False, widget=forms.Textarea)

    have_rules = forms.BooleanField(required=False)
    preview_rules = forms.BooleanField(required=False)
    rules = forms.CharField(max_length=20000, required=False, widget=forms.Textarea)

    start_date = forms.DateTimeField()
    submission_deadline_date = forms.DateTimeField()

    have_listening_party = forms.BooleanField(required=False)
    party_immediately = forms.BooleanField(required=False)
    listening_party_date = forms.DateTimeField(required=False)

    vote_time_quantity = forms.IntegerField(max_value=12, min_value=1, initial=1)
    vote_time_measurement = forms.ChoiceField(choices=TIME_QUANTIFIERS, initial=WEEKS)

    # add this many hours to the times to get the correct value
    tz_offset = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = self.cleaned_data

        in_lp_date = cleaned_data.get('listening_party_date')
        in_have_party = cleaned_data.get('have_listening_party')
        in_deadline = cleaned_data.get('submission_deadline_date')
        in_start_date = cleaned_data.get('start_date')

        # clean start_date
        if in_start_date <= datetime.now():
            msg = u"You cannot start a competition in the past."
            self._errors['start_date'] = self.error_class([msg])

        # clean submission_deadline_date
        min_deadline = in_start_date + timedelta(minutes=10)
        if in_deadline < min_deadline:
            msg = u"You have to give people at least 10 minutes to work."
            self._errors['submission_deadline_date'] = self.error_class([msg])

        # clean listening_party_date
        if not cleaned_data.get('party_immediately'):
            if in_have_party:
                if in_lp_date is None:
                    msg = u"If you want a listening party, you need to set a date."
                    self._errors['listening_party_date'] = self.error_class([msg])
                elif in_lp_date < in_deadline:
                    msg = u"Listening party must be after submission deadline."
                    self._errors['listening_party_date'] = self.error_class([msg])
        
        return cleaned_data

