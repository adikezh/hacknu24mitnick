from django.urls import path

from courses.views import BasePage

urlpatterns = [
    path("", BasePage.as_view())
]
