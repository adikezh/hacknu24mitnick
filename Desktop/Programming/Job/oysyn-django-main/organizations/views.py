from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Organization
from users.mixins import OwnerPermissionMixin, StaffRequiredMixin, ModeratorRequiredMixin


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organizations/organization_list.html'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        """
        Return all organizations if the user is a superuser.
        Otherwise, filter organizations created by the current user.
        """
        if self.request.user.is_superuser:
            return Organization.objects.all().order_by('title')
        return Organization.objects.filter(created_by=self.request.user).order_by('title')
    

class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'organizations/organization_detail.html'


class OrganizationCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Organization
    template_name = 'organizations/organization_form.html'
    fields = ['title', 'city', 'address', 'description', 'logo',]
    success_url = reverse_lazy('organizations:organization_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class OrganizationUpdateView(LoginRequiredMixin, ModeratorRequiredMixin, UpdateView):
    model = Organization
    template_name = 'organizations/organization_form.html'
    fields = [
        'title', 'description', 'city', 'address', 'logo',
        'article_threshold', 'course_work_threshold', 'doctoral_threshold',
        'diploma_thesis_threshold', 'diploma_project_threshold', 'masters_thesis_threshold',
        'study_guide_threshold', 'textbook_threshold', 'book_threshold', 'research_threshold',
        'monograph_threshold', 'abstract_threshold', 'other_threshold',
    ]
    success_url = reverse_lazy('organizations:organization_list')


class OrganizationDeleteView(LoginRequiredMixin, OwnerPermissionMixin, DeleteView):
    model = Organization
    template_name = 'organizations/organization_confirm_delete.html'
    success_url = reverse_lazy('organizations:organization_list')
