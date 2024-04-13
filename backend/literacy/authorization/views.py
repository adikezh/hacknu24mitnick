from typing import Any

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from authorization.forms import UserLoginForm, UserRegisterForm


# Create your views here.


class UserLoginView(LoginView):
    template_name = "account/login.html"
    authentication_form = UserLoginForm
    redirect_authenticated_user = True
    next_page = reverse_lazy("account:home")


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("account:home")


class UserRegisterView(CreateView):
    template_name = "account/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("account:home")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Create user and login if form valid"""
        valid = super().form_valid(form)
        login(self.request, self.object)
        return valid

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        """Redirect authenticated user"""
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        return super().get(request, *args, **kwargs)
