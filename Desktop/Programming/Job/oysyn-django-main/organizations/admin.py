from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'created_by', 'checks_available')
    search_fields = ('title', 'city', 'created_by__username',)
    list_filter = ('city',)
    ordering = ('title',)
    # readonly_fields = ('created_by',)

    fieldsets = (
        (None, {
            'fields': ('title', 'city', 'address', 'description', 'checks_available', 'logo')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('created_by',),
        }),
    )