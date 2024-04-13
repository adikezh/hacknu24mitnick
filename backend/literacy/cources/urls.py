from django.urls import path

from authorization.views import UserLoginView, UserLogoutView, UserRegisterView

urlpatterns = [
    path("/login", UserLoginView.as_view()),
    path("/register", UserRegisterView.as_view()),
    path("/logout", UserLogoutView.as_view())
]
