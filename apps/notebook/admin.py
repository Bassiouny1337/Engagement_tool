from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "engagement", "parent", "updated_at", "updated_by")
    list_filter = ("engagement",)
    search_fields = ("title", "content")
    autocomplete_fields = ("engagement", "parent")
