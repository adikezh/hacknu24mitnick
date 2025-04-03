from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'username', 'role',) 

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role not in [choice[0] for choice in get_user_model().Role.choices]:
            raise ValidationError("Invalid role selected.")
        return role

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'middle_name', 'iin', 'city', 'address', 'zip_code')

    def clean_iin(self):
        iin = str(self.cleaned_data.get('iin'))  # Convert to string
        if not iin.isdigit() or len(iin) != 12:
            raise forms.ValidationError("IIN must be exactly 12 digits.")
        return iin

        
    def clean_zip_code(self):
        zip_code = self.cleaned_data.get('zip_code')
        if not zip_code.isdigit() or len(zip_code) < 5:
            raise forms.ValidationError("Zip code must be at least 5 digits")
        return zip_code
    
