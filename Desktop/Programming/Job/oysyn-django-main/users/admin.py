from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = ['email', 'role', 'is_staff', 'is_active',
                    'organization', 'checks_available', 'reports_count']
    list_filter = ['role', 'is_staff', 'is_active', 'organization']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'organization', 'checks_available')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'checks_available')}),
    )

    def get_queryset(self, request):
        """
        Override the queryset to annotate it with the count of reports.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(reports_count=Count('report'))
        return queryset
    
    def reports_count(self, obj):
        """
        Custom method to display the reports count.
        """
        return obj.reports_count
    reports_count.admin_order_field = 'reports_count'
    reports_count.short_description = 'Reports Count'

admin.site.register(CustomUser, CustomUserAdmin)
