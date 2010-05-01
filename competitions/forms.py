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

    def clean_submission_deadline_date(self):
        in_start_date = self.cleaned_data['start_date']
        in_deadline = self.cleaned_data['submission_deadline_date']

        min_deadline = in_start_date + timedelta(minutes=10)
        if in_deadline < min_deadline:
            raise forms.ValidationError("You have to give people at least 10 minutes to work.")

        return in_deadline

    def clean_listening_party_date(self):
        if self.cleaned_data['party_immediately'] or not self.cleaned_data.has_key('submission_deadline_date'):
            return self.cleaned_data['listening_party_date']
        in_date = self.cleaned_data['listening_party_date']
        in_have_party = self.cleaned_data['have_listening_party']
        in_deadline = self.cleaned_data['submission_deadline_date']
        if in_have_party:
            if in_date is None:
                raise forms.ValidationError("If you want a listening party, you need to set a date.")
            if in_date < in_deadline:
                raise forms.ValidationError("Listening party must be after submission deadline.")
        return in_date

