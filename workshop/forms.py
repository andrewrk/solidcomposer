from django import forms
from workshop import design

class NewProjectForm(forms.Form):
    title = forms.CharField(max_length=100, error_messages={'required': design.this_field_is_required})
    file_source = forms.FileField(label="Project file", error_messages={ 'required': design.this_field_is_required})
    file_mp3 = forms.FileField(label="MP3 Preview", required=False)
    comments = forms.CharField(max_length=1000, required=False, widget=forms.Textarea)

    def clean_file_mp3(self):
        filename = self.cleaned_data['file_mp3']

        if filename is None:
            return filename

        if filename.name[-3:].lower() != 'mp3':
            raise forms.ValidationError(design.uploaded_file_must_be_mp3)

        return filename

class NewBandForm(forms.Form):
    band_name = forms.CharField(max_length=100, error_messages={'required': design.this_field_is_required})

class RenameBandForm(forms.Form):
    new_name = forms.CharField(max_length=100, error_messages={'required': design.this_field_is_required})

class RenameProjectForm(forms.Form):
    title = forms.CharField(max_length=100, error_messages={'required': design.you_must_have_a_title})
    comments = forms.CharField(max_length=1000, required=False, widget=forms.Textarea)
    project = forms.IntegerField()
