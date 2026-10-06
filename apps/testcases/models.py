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
    """Create TestCase rows for a domain from the checklist template.

    Idempotent: skips titles that already exist for this engagement+domain.
    Returns the number of test cases created.
    """
    existing = set(
        TestCase.objects.filter(
            engagement=engagement, domain_key=domain_key
        ).values_list("category", "title")
    )
    created = 0
    order = 0
    to_create = []
    for category, title in seed_test_cases(domain_key):
        order += 1
        if (category, title) in existing:
            continue
        to_create.append(
            TestCase(
                engagement=engagement,
                domain_key=domain_key,
                category=category,
                title=title,
                order=order,
                updated_by=created_by,
            )
        )
        created += 1
    TestCase.objects.bulk_create(to_create)
    return created
