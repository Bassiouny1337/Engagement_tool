"""Test cases: the per-domain checklist items tracked on an engagement."""
from django.conf import settings
from django.db import models

from apps.domains.constants import DOMAIN_CHOICES, seed_test_cases


class TestCase(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        PASS = "pass", "Pass (no issue)"
        FAIL = "fail", "Fail (issue found)"
        NA = "na", "N/A"
        BLOCKED = "blocked", "Blocked"

    # Statuses that count as "done" for progress calculations.
    DONE_STATUSES = {Status.PASS, Status.FAIL, Status.NA}

    engagement = models.ForeignKey(
        "engagements.Engagement", on_delete=models.CASCADE, related_name="test_cases"
    )
    domain_key = models.CharField(max_length=20, choices=DOMAIN_CHOICES)
    category = models.CharField(max_length=120)
    title = models.CharField(max_length=255)
    source_scenario = models.ForeignKey(
        "catalog.Scenario", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="imported_test_cases",
    )
    asset = models.ForeignKey(
        "assets.Asset", null=True, blank=True, on_delete=models.CASCADE,
        related_name="test_cases",
    )
    function = models.ForeignKey(
        "assets.Function", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="test_cases",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_test_cases",
    )
    notes = models.TextField(blank=True)
    is_custom = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("domain_key", "category", "order", "id")

    def __str__(self):
        return f"[{self.get_domain_key_display()}] {self.title}"

    @property
    def is_done(self):
        return self.status in self.DONE_STATUSES


def seed_engagement_domain(engagement, domain_key, created_by=None):
    """Create TestCase rows for a domain from the DB checklist template.

    Reads active catalog.ChecklistItem rows for the domain (falling back to the
    bundled constants if the catalog is empty, e.g. before bootstrap).
    Idempotent: skips (category, title) pairs that already exist for this
    engagement+domain. Returns the number of test cases created.
    """
    from apps.catalog.models import ChecklistItem

    existing = set(
        TestCase.objects.filter(
            engagement=engagement, domain_key=domain_key
        ).values_list("category", "title")
    )

    items = list(
        ChecklistItem.objects.filter(
            domain_key=domain_key, is_active=True, owner__isnull=True
        ).values_list("category", "title", "guidance", "order")
    )
    if not items and not ChecklistItem.objects.filter(
        domain_key=domain_key, owner__isnull=True
    ).exists():
        # Fallback only when the catalog has no rows at all for this domain
        # (e.g. a fresh install before bootstrap). If rows exist but are all
        # inactive, that is a deliberate choice — seed nothing.
        items = [(c, t, "", i) for i, (c, t) in enumerate(seed_test_cases(domain_key))]

    to_create = []
    for category, title, guidance, order in items:
        if (category, title) in existing:
            continue
        to_create.append(
            TestCase(
                engagement=engagement,
                domain_key=domain_key,
                category=category,
                title=title,
                notes=guidance or "",
                order=order,
                updated_by=created_by,
            )
        )
    TestCase.objects.bulk_create(to_create)
    return len(to_create)


def import_scenario(engagement, scenario, created_by=None, category="Imported scenarios"):
    """Create a TestCase on an engagement from a catalog Scenario."""
    tc = TestCase.objects.create(
        engagement=engagement,
        domain_key=scenario.domain_key,
        category=category,
        title=scenario.title,
        notes=scenario.as_testcase_notes(),
        source_scenario=scenario,
        is_custom=True,
        updated_by=created_by,
    )
    return tc
