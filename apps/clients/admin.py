from django.contrib import admin

from .models import ClientOrg


@admin.register(ClientOrg)
class ClientOrgAdmin(admin.ModelAdmin):
    list_display = ("name", "primary_contact_name", "primary_contact_email", "created_at")
    search_fields = ("name", "primary_contact_name", "primary_contact_email")
