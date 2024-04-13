from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from authorization.models import User


class UserLoginForm(AuthenticationForm):
    ...


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label="Username", max_length=50, required=True)
    email = forms.EmailField(label="E-mail", required=True)

    class Meta:
        model = User
        fields = ["username", "email"]
