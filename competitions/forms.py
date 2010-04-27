from django import forms

from opensourcemusic.competitions.models import *

HOURS, DAYS, WEEKS = range(3)

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
    listening_party_date = forms.DateTimeField(required=False)

    vote_time_quantity = forms.IntegerField(max_value=12, min_value=1, initial=1)
    vote_time_measurement = forms.ChoiceField(choices=TIME_QUANTIFIERS, initial=WEEKS)

