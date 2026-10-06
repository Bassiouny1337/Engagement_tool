"""Engagement, scope, in-scope domains, and team assignment models."""
from django.conf import settings
from django.db import models

from apps.domains.constants import DOMAIN_CHOICES


class Engagement(models.Model):
    class Status(models.TextChoices):
        SCOPING = "scoping", "Scoping"
        ACTIVE = "active", "Active"
        REVIEW = "review", "In Review"
        DELIVERED = "delivered", "Delivered"
        CLOSED = "closed", "Closed"

    # Allowed lifecycle transitions (forward flow + reopen to active).
    TRANSITIONS = {
        Status.SCOPING: {Status.ACTIVE, Status.CLOSED},
        Status.ACTIVE: {Status.REVIEW, Status.CLOSED},
        Status.REVIEW: {Status.ACTIVE, Status.DELIVERED},
        Status.DELIVERED: {Status.CLOSED, Status.ACTIVE},
        Status.CLOSED: {Status.ACTIVE},
    }

    client = models.ForeignKey(
        "clients.ClientOrg", on_delete=models.PROTECT, related_name="engagements"
    )
    title = models.CharField(max_length=200)
    code = models.SlugField(max_length=40, unique=True, help_text="Short reference, e.g. ACME-2026-01")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCOPING)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="created_engagements",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="TeamAssignment", related_name="engagements"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.code} — {self.title}"

    def can_transition_to(self, new_status):
        if new_status == self.status:
            return True
        return new_status in self.TRANSITIONS.get(self.status, set())

    @property
    def domain_keys(self):
        return list(self.domains.values_list("domain_key", flat=True))


class EngagementDomain(models.Model):
    """A domain that is in scope for an engagement."""

    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, related_name="domains"
    )
    domain_key = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("engagement", "domain_key")
        ordering = ("domain_key",)

    def __str__(self):
        return f"{self.engagement.code}:{self.get_domain_key_display()}"


class ScopeItem(models.Model):
    """A target in (or explicitly out of) scope for an engagement."""

    class Kind(models.TextChoices):
        IP = "ip", "IP / CIDR"
        HOST = "host", "Hostname"
        URL = "url", "URL"
        SSID = "ssid", "Wi-Fi SSID"
        DOMAIN = "ad_domain", "AD Domain"
        DEVICE = "device", "Device / Asset"
        OTHER = "other", "Other"

    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, related_name="scope_items"
    )
    domain_key = models.CharField(max_length=20, choices=DOMAIN_CHOICES, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.IP)
    value = models.CharField(max_length=255)
    in_scope = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-in_scope", "kind", "value")

    def __str__(self):
        flag = "" if self.in_scope else "OUT "
        return f"{flag}{self.value}"


class TeamAssignment(models.Model):
    """Membership of a user on an engagement, with a per-engagement role."""

    class EngagementRole(models.TextChoices):
        LEAD = "lead", "Lead"
        TESTER = "tester", "Tester"
        REVIEWER = "reviewer", "Reviewer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="team_assignments",
    )
    engagement = models.ForeignKey(
        Engagement, on_delete=models.CASCADE, related_name="team_assignments"
    )
    engagement_role = models.CharField(
        max_length=20, choices=EngagementRole.choices, default=EngagementRole.TESTER
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "engagement")
        ordering = ("engagement", "engagement_role")

    def __str__(self):
        return f"{self.user} @ {self.engagement.code} ({self.get_engagement_role_display()})"
