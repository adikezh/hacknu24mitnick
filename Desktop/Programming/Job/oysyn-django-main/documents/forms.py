from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Document, Folder


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'parent_folder']


class DocumentForm(forms.ModelForm):
    LANGUAGES = [
        ('eng', _('English')),
        ('rus', _('Russian')),
        ('kaz', _('Kazakh')),
        # Add other languages as needed
    ]
    ocr_languages = forms.MultipleChoiceField(
        choices=LANGUAGES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("OCR languages"),
        help_text=_("Select languages for OCR processing")
    )

    class Meta:
        model = Document
        fields = ['title', 'author', 'document_type', 'department', 'document',
                  'include_ocr', 'ocr_languages', 'folder']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Pass the user explicitly
        super().__init__(*args, **kwargs)
        if user:
            # Filter folders to show only the user's folders
            self.fields['folder'].queryset = Folder.objects.filter(created_by=user)
    
    def clean_document(self):
        document = self.cleaned_data.get('document')
        if document:
            if len(document.name) > 255:
                raise ValidationError(_('The filename is too long. Please use a shorter name.'))
        return document

class DocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'author', 'document_type', 'department']
        labels = {
            'title': 'Название документа',
            'author': 'Автор',
            'doc_type': 'Тип',
            'department': 'Подразделение',
        }