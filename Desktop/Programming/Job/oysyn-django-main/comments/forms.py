from django import forms
from .models import Comment


class CommentForm(forms.ModelForm):
    report_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Comment
        fields = ['text', 'report_id',]
