from django.contrib import messages
from django.contrib.auth import login, get_user_model, get_backends
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView

from .forms import CustomUserChangeForm


User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    """View to display detailed information about user."""
    model = User
    template_name = 'user_detail.html'

    def get_object(self):
        return self.request.user


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """View to update user's information."""
    model = User
    template_name = 'user_update.html'
    form_class = CustomUserChangeForm
    success_url = reverse_lazy('user_detail')

    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'failure', 'errors': form.errors}, status=400)
        return response


@login_required
def impersonate_user(request, user_id):
    """
    Allows superusers to impersonate any user, and moderators to impersonate
    experts within their organization.
    """
    target_user = get_object_or_404(User, id=user_id)

    # Permission checks
    if request.user.is_superuser:
        pass
    elif request.user.is_moderator:
        if target_user.organization != request.user.organization:
            messages.error(request, "Вы не можете имперсонировать пользователей \
                           другой организации.")
            return redirect("home")
    else:
        messages.error(request, "У вас недостаточно прав, чтобы имперсонировать \
                       пользователя.")
        return redirect("home")

    # Store original user in session if not already set
    if "original_user_id" not in request.session:
        request.session["original_user_id"] = request.user.id

    # Assign the backend explicitly
    backend = request.session.get('_auth_user_backend', 'django.contrib.auth.backends.ModelBackend')
    target_user.backend = backend

    # Log in as the target user
    login(request, target_user, backend=backend)
    messages.info(request, f"Вы имперсонировали пользователя {target_user.email}.")
    return redirect("home")


@login_required
def stop_impersonation(request):
    """
    Stops impersonation and returns to the original user.
    """
    original_user_id = request.session.pop('original_user_id', None)
    if not original_user_id:
        messages.error(request, "Вы не имперсонировали пользователя.")
        return redirect("home")

    # Get the original user and restore session
    original_user = get_object_or_404(User, id=original_user_id)
    backend = request.session.get('_auth_user_backend', 'django.contrib.auth.backends.ModelBackend')
    original_user.backend = backend

    # Log back in as the original user
    login(request, original_user, backend=backend)
    messages.info(request, f"You have returned to your account {original_user.email}.")
    return redirect("home")
