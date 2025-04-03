from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter

from .models import Document, Report, PlagiarismInstance


class PlagiarismInstanceInline(admin.TabularInline):
    model = PlagiarismInstance
    extra = 1


class ReportInline(admin.TabularInline):
    model = Report
    fields = (
        'title',
        'internet_originality_percentage', 
        'internet_plagiarism_percentage',
        'originality_percentage',
        'plagiarism_percentage',
    )
    extra = 1  # Number of empty forms to display
    

class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'final_originality',
                    'final_plagiarism', 'citation_percentage', 'selfcitation_percentage')
    # inlines = [PlagiarismInstanceInline]
    search_fields = ('title', 'document__title', 'created_by__email')
    list_filter = ('document__document_type', 'created_at', 'created_by',)

    def final_originality(self, obj):
        """Display the calculated final originality percentage."""
        return obj.calculate_final_originality()
    final_originality.short_description = 'Final Originality'

    def final_plagiarism(self, obj):
        """Display the calculated final plagiarism percentage."""
        return obj.calculate_final_plagiarism()
    final_plagiarism.short_description = 'Final Plagiarism'


class DocumentAdmin(admin.ModelAdmin):
    inlines = [ReportInline]
    list_display = ('title', 'created_by', 'created_at', 'status', 'tasks_completed')


@admin.register(PlagiarismInstance)
class PlagiarismInstanceAdmin(admin.ModelAdmin):
    list_display = ('report', 'plagiarism_percentage', 'url', 'type',
                    'module', 'created_at')
    list_filter = ('type', 'module', 'report__document__created_by')
    search_fields = ('url', 'report__title', 'report__document__title',
                     'report__document__author', 'report__id')
    # ordering = ('-plagiarism_percentage',)
    
    def created_at(self, obj):
        return obj.report.created_at
    created_at.short_description = 'Created At'
    created_at.admin_order_field = 'report__created_at'


admin.site.register(Document, DocumentAdmin)
admin.site.register(Report, ReportAdmin)
