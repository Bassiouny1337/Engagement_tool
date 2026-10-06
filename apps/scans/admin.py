from django.contrib import admin

from .models import Scan


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("filename", "engagement", "host_count", "open_port_count", "created_at")
    list_filter = ("engagement",)
    search_fields = ("filename", "args")
    readonly_fields = ("data",)
