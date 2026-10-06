from django.contrib import admin

from .models import TestCase


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ("title", "engagement", "domain_key", "category", "status", "assignee")
    list_filter = ("status", "domain_key", "engagement")
    search_fields = ("title", "category")
    list_editable = ("status",)
    autocomplete_fields = ("engagement", "assignee")
