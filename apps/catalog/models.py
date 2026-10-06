"""Super-admin curated catalog: checklist templates and the scenario library.

- ChecklistItem: the per-domain checklist template rows. When a domain is added
  to an engagement, active items for that domain are copied into TestCases.
- Scenario: a reusable knowledge-base entry (a scenario faced before) with
  steps, payloads, references and tags. Pentesters pull one into an engagement
  as a test case.
"""
from django.conf import settings
from django.db import models

from apps.domains.constants import DOMAIN_CHOICES


class ChecklistItem(models.Model):
    """A template checklist row for a domain, managed by the super admin."""

    domain_key = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    category = models.CharField(max_length=120)
    title = models.CharField(max_length=255)
    guidance = models.TextField(
        blank=True, help_text="How to test / what to look for (copied into the test case notes)."
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("domain_key", "category", "order", "id")
        indexes = [models.Index(fields=["domain_key", "is_active"])]

    def __str__(self):
        return f"[{self.get_domain_key_display()}] {self.category} / {self.title}"


class Scenario(models.Model):
    """A reusable test scenario captured from past engagements."""

    title = models.CharField(max_length=255)
    domain_key = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    summary = models.TextField(help_text="What this scenario tests, in one or two lines.")
    steps = models.TextField(blank=True, help_text="Reproduction / testing steps.")
    payloads = models.TextField(blank=True, help_text="Payloads, commands, or tooling.")
    references = models.TextField(blank=True, help_text="Links / CVEs / write-ups (one per line).")
    tags = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated tags, e.g. ssrf, cloud, idor"
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("domain_key", "title")
        indexes = [models.Index(fields=["domain_key", "is_active"])]

    def __str__(self):
        return f"[{self.get_domain_key_display()}] {self.title}"

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def as_testcase_notes(self):
        """Render the scenario body as a notes block for an imported test case."""
        parts = [self.summary.strip()]
        if self.steps.strip():
            parts.append("Steps:\n" + self.steps.strip())
        if self.payloads.strip():
            parts.append("Payloads:\n" + self.payloads.strip())
        if self.references.strip():
            parts.append("References:\n" + self.references.strip())
        return "\n\n".join(p for p in parts if p)
