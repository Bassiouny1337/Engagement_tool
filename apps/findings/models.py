"""Findings: vulnerabilities discovered during an engagement."""
from django.conf import settings
from django.db import models

from apps.domains.constants import DOMAIN_CHOICES


class Finding(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"
        INFO = "info", "Informational"

    # Lower number = more severe (for ordering / sorting).
    SEVERITY_ORDER = {
        Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2,
        Severity.LOW: 3, Severity.INFO: 4,
    }

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CONFIRMED = "confirmed", "Confirmed"
        REMEDIATED = "remediated", "Remediated"
        ACCEPTED = "accepted", "Risk accepted"
        FALSE_POSITIVE = "false_positive", "False positive"

    engagement = models.ForeignKey(
        "engagements.Engagement", on_delete=models.CASCADE, related_name="findings"
    )
    title = models.CharField(max_length=255)
    domain_key = models.CharField(max_length=20, choices=DOMAIN_CHOICES, blank=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    cvss_vector = models.CharField(max_length=120, blank=True)
    cvss_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    affected = models.TextField(blank=True, help_text="Affected hosts / URLs / assets, one per line.")
    description = models.TextField(blank=True)
    impact = models.TextField(blank=True)
    remediation = models.TextField(blank=True)
    references = models.TextField(blank=True, help_text="Links / CVEs, one per line.")

    source_test_case = models.ForeignKey(
        "testcases.TestCase", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="findings",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_findings",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="reviewed_findings",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"

    @property
    def severity_rank(self):
        return self.SEVERITY_ORDER.get(self.severity, 99)

    @property
    def is_reviewed(self):
        return self.reviewed_by_id is not None
