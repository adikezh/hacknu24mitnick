from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect

from .models import CustomUser
from .views import UserDetailView

class ModeratorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == CustomUser.Role.MODERATOR


class ExpertRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == CustomUser.Role.EXPERT


class OwnerPermissionMixin:
    def get_object(self, queryset=None):
        """Restrict access to the object to only its owner."""
        obj = super().get_object()
        if obj.created_by != self.request.user:
            raise PermissionDenied("You are not allowed to access this resource.")
        return obj


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to staff users only."""

    def test_func(self) -> bool | None:
        return self.request.user.is_staff
    
    def handle_no_permission(self) -> HttpResponseRedirect:
        return redirect('UserDetailView')
