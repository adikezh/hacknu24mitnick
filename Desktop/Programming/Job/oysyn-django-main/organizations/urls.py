from django.urls import path
from .views import (OrganizationListView, OrganizationDetailView,
                    OrganizationCreateView, OrganizationUpdateView,
                    OrganizationDeleteView)

app_name = 'organizations'

urlpatterns = [
    path('list/', OrganizationListView.as_view(), name='organization_list'),
    path('detail/<int:pk>/', OrganizationDetailView.as_view(), name='organization_detail'),
    path('create/', OrganizationCreateView.as_view(), name='organization_create'),
    path('update/<int:pk>/', OrganizationUpdateView.as_view(), name='organization_update'),
    path('<pk>/delete/', OrganizationDeleteView.as_view(), name='organization_delete'),
]