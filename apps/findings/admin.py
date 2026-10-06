from django.contrib import admin

from .models import Finding


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ("title", "engagement", "severity", "status", "reviewed_by", "created_at")
    list_filter = ("severity", "status", "engagement")
    search_fields = ("title", "description", "remediation")
    autocomplete_fields = ("engagement", "source_test_case")
