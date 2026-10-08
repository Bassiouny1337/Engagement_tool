from django.contrib import admin

from .models import Asset, Credential, FileArtifact, Function, Service


class CredentialInline(admin.TabularInline):
    model = Credential
    extra = 0
    exclude = ("secret_encrypted",)


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0


class FileInline(admin.TabularInline):
    model = FileArtifact
    extra = 0


class FunctionInline(admin.TabularInline):
    model = Function
    extra = 0


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "engagement", "asset_type", "primary_target")
    list_filter = ("asset_type", "engagement")
    search_fields = ("name", "primary_target", "description")
    inlines = [FunctionInline, ServiceInline, FileInline, CredentialInline]
