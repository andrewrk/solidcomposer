from competitions import design
from datetime import datetime, timedelta
from django import forms
from django.conf import settings

class TimeUnit:
    HOURS, DAYS, WEEKS = range(3)

    seconds_multiplier = {
        HOURS: 60*60,
        DAYS: 24*60*60,
        WEEKS: 7*24*60*60,
    }

class SubmitEntryForm(forms.Form):
    title = forms.CharField(max_length=100, error_messages={
        'required': design.this_field_is_required})
    comments = forms.CharField(max_length=1000, required=False, widget=forms.Textarea)
    file_mp3 = forms.FileField(error_messages={
        'required': design.this_field_is_required})
    file_source = forms.FileField(required=False)

    def clean_file_mp3(self):
        filename = self.cleaned_data['file_mp3']

        if filename[-3:].lower() != 'mp3':
            raise forms.ValidationError(design.uploaded_file_must_be_mp3)

        return filename

class CreateCompetitionForm(forms.Form):
    TIME_QUANTIFIERS = (
        (TimeUnit.HOURS, "hours"),
        (TimeUnit.DAYS, "days"),
        (TimeUnit.WEEKS, "weeks"),
    )

    title = forms.CharField(max_length=100, error_messages={'required': design.this_field_is_required})

    have_theme = forms.BooleanField(required=False)
    preview_theme = forms.BooleanField(required=False)
    theme = forms.CharField(max_length=20000, required=False, widget=forms.Textarea)

    have_rules = forms.BooleanField(required=False)
    preview_rules = forms.BooleanField(required=False)
    rules = forms.CharField(max_length=20000, required=False, widget=forms.Textarea)

    start_date = forms.DateTimeField(error_messages={'required': design.this_field_is_required})
    submission_deadline_date = forms.DateTimeField(error_messages={'required': design.this_field_is_required})

    have_listening_party = forms.BooleanField(required=False)
    party_immediately = forms.BooleanField(required=False)
    listening_party_date = forms.DateTimeField(required=False)

    vote_time_quantity = forms.IntegerField(max_value=12, min_value=1, initial=1, error_messages={'required': design.this_field_is_required})
    vote_time_measurement = forms.ChoiceField(choices=TIME_QUANTIFIERS, initial=TimeUnit.WEEKS, error_messages={'required': design.this_field_is_required})

    # add this many hours to the times to get the correct value
    tz_offset = forms.IntegerField(widget=forms.HiddenInput(), error_messages={'required': design.this_field_is_required})

    def _clean_start_date(self, in_start_date):
        if in_start_date <= datetime.now():
            msg = design.cannot_start_compo_in_the_past
            self._errors['start_date'] = self.error_class([msg])

    def clean(self):
        cleaned_data = self.cleaned_data

        in_lp_date = cleaned_data.get('listening_party_date')
        in_have_party = cleaned_data.get('have_listening_party')
        in_deadline = cleaned_data.get('submission_deadline_date')
        in_start_date = cleaned_data.get('start_date')
        in_tz_offset = cleaned_data.get('tz_offset')

        if in_tz_offset is None:
            msg = design.this_field_is_required
            self._errors['tz_offset'] = self.error_class([msg])
            return cleaned_data

        # adjust dates with tz_offset
        tz_delta = timedelta(hours=in_tz_offset)

        if in_lp_date is not None:
            in_lp_date += tz_delta
        if in_deadline is not None:
            in_deadline += tz_delta
        if in_start_date is not None:
            in_start_date += tz_delta

        if in_start_date is None:
            msg = design.this_field_is_required
            self._errors['start_date'] = self.error_class([msg])
            return cleaned_data

        self._clean_start_date(in_start_date)

        # clean submission_deadline_date
        min_deadline = in_start_date + timedelta(minutes=settings.MINIMUM_COMPO_LENGTH)
        if in_deadline < min_deadline:
            msg = design.give_at_least_x_minutes_to_work
            self._errors['submission_deadline_date'] = self.error_class([msg])

        # clean listening_party_date
        if not cleaned_data.get('party_immediately'):
            if in_have_party:
                if in_lp_date is None:
                    msg = design.if_you_want_lp_set_date
                    self._errors['listening_party_date'] = self.error_class([msg])
                elif in_lp_date < in_deadline:
                    msg = design.lp_gt_submission_deadline
                    self._errors['listening_party_date'] = self.error_class([msg])
        
        return cleaned_data

class EditCompetitionForm(CreateCompetitionForm):
    def _clean_start_date(self, in_start_date):
        pass

