from django.urls import path
from . import views


urlpatterns = [
    path('profile/', views.UserDetailView.as_view(), name='user_detail'),
    path('profile/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('impersonate/<int:user_id>/', views.impersonate_user, name="impersonate_user"),
    path('stop-impersonation/', views.stop_impersonation, name="stop_impersonation"),
]
