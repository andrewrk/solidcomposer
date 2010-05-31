from django import forms

from opensourcemusic.workshop.models import *
from opensourcemusic.workshop import design

class NewProjectForm(forms.Form):
    title = forms.CharField(max_length=100,
        error_messages={'required': design.this_field_is_required})
    file_source = forms.FileField(error_messages={
        'required': design.this_field_is_required})
    file_mp3 = forms.FileField(error_messages={
        'required': design.this_field_is_required})
    comments = forms.CharField(max_length=1000, required=False,
        widget=forms.Textarea)

    def clean_file_mp3(self):
        filename = self.cleaned_data['file_mp3']

        if filename.name[-3:].lower() != 'mp3':
            raise forms.ValidationError(design.uploaded_file_must_be_mp3)

        return filename

