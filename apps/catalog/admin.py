from django.contrib import admin

from .models import ChecklistItem, Scenario


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("title", "domain_key", "category", "order", "is_active")
    list_filter = ("domain_key", "is_active", "category")
    search_fields = ("title", "category", "guidance")
    list_editable = ("order", "is_active")


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("title", "domain_key", "tags", "is_active", "updated_at")
    list_filter = ("domain_key", "is_active")
    search_fields = ("title", "summary", "steps", "payloads", "tags")
