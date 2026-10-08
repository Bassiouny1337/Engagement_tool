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
    """A checklist row for a domain.

    owner is NULL for global (shared) items managed by the super admin, and set
    to a user for that pentester's personal items. When a domain is added to an
    engagement, active *global* items for that domain are copied into TestCases.
    """

    domain_key = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    category = models.CharField(max_length=120)
    title = models.CharField(max_length=255)
    guidance = models.TextField(
        blank=True, help_text="How to test / what to look for (copied into the test case notes)."
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE,
        related_name="personal_checklist_items",
        help_text="Null = global/shared; set = personal to this user.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("domain_key", "category", "order", "id")
        indexes = [models.Index(fields=["domain_key", "is_active", "owner"])]

    def __str__(self):
        scope = "personal" if self.owner_id else "global"
        return f"[{self.get_domain_key_display()}] {self.category} / {self.title} ({scope})"

    @property
    def is_global(self):
        return self.owner_id is None


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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE,
        related_name="personal_scenarios",
        help_text="Null = global/shared; set = personal to this user.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("domain_key", "title")
        indexes = [models.Index(fields=["domain_key", "is_active", "owner"])]

    def __str__(self):
        return f"[{self.get_domain_key_display()}] {self.title}"

    @property
    def is_global(self):
        return self.owner_id is None

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


class ContributionRequest(models.Model):
    """A pentester's request to promote a personal item into the global catalog.

    On approval, the personal item is COPIED to a new global item (owner=None);
    the requester keeps their personal copy.
    """

    class Kind(models.TextChoices):
        CHECKLIST = "checklist", "Checklist item"
        SCENARIO = "scenario", "Scenario"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    checklist_item = models.ForeignKey(
        ChecklistItem, null=True, blank=True, on_delete=models.CASCADE,
        related_name="contribution_requests",
    )
    scenario = models.ForeignKey(
        Scenario, null=True, blank=True, on_delete=models.CASCADE,
        related_name="contribution_requests",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="contribution_requests",
    )
    note = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    decision_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    # The global copy produced on approval (for traceability).
    promoted_checklist_item = models.ForeignKey(
        ChecklistItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    promoted_scenario = models.ForeignKey(
        Scenario, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_kind_display()} by {self.requested_by} — {self.status}"

    @property
    def source(self):
        return self.checklist_item if self.kind == self.Kind.CHECKLIST else self.scenario

    def approve(self, by_user):
        """Copy the personal item into the global catalog; keep the personal one."""
        from django.utils import timezone

        if self.status != self.Status.PENDING:
            return None
        if self.kind == self.Kind.CHECKLIST and self.checklist_item:
            src = self.checklist_item
            self.promoted_checklist_item = ChecklistItem.objects.create(
                domain_key=src.domain_key, category=src.category, title=src.title,
                guidance=src.guidance, order=src.order, is_active=True,
                owner=None, created_by=by_user,
            )
        elif self.kind == self.Kind.SCENARIO and self.scenario:
            src = self.scenario
            self.promoted_scenario = Scenario.objects.create(
                title=src.title, domain_key=src.domain_key, summary=src.summary,
                steps=src.steps, payloads=src.payloads, references=src.references,
                tags=src.tags, is_active=True, owner=None, created_by=by_user,
            )
        self.status = self.Status.APPROVED
        self.decided_by = by_user
        self.decided_at = timezone.now()
        self.save()
        return self.promoted_checklist_item or self.promoted_scenario

    def reject(self, by_user, note=""):
        from django.utils import timezone

        if self.status != self.Status.PENDING:
            return
        self.status = self.Status.REJECTED
        self.decided_by = by_user
        self.decision_note = note[:255]
        self.decided_at = timezone.now()
        self.save()
