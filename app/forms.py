from django import forms

class UploadPDFForm(forms.Form):
    exam_name = forms.CharField(max_length=255)
    pat = forms.CharField(max_length=100)
    subject_name = forms.CharField(max_length=255)
    original_pdf = forms.FileField()
