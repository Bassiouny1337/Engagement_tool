from django.contrib import admin

from .models import Engagement, EngagementDomain, ScopeItem, TeamAssignment


class EngagementDomainInline(admin.TabularInline):
    model = EngagementDomain
    extra = 0


class ScopeItemInline(admin.TabularInline):
    model = ScopeItem
    extra = 0


class TeamAssignmentInline(admin.TabularInline):
    model = TeamAssignment
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "client", "status", "start_date", "end_date")
    list_filter = ("status", "client")
    search_fields = ("code", "title", "client__name")
    prepopulated_fields = {"code": ("title",)}
    inlines = [EngagementDomainInline, ScopeItemInline, TeamAssignmentInline]


@admin.register(TeamAssignment)
class TeamAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "engagement", "engagement_role", "assigned_at")
    list_filter = ("engagement_role",)
    autocomplete_fields = ("user", "engagement")
