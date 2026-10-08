"""Custom user model and role definitions.

Roles give capabilities (what kind of action a user may perform); engagement
membership (apps.engagements.TeamAssignment) gives reach (which engagements a
user may touch). The two are always checked together for object-level actions.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin / Owner"
    MANAGER = "manager", "Engagement Manager"
    PENTESTER = "pentester", "Pentester"
    REVIEWER = "reviewer", "Technical Reviewer / QA"
    AUDITOR = "auditor", "Read-only Auditor"


# Capability matrix. Object-level reach is enforced separately via engagement
# membership; these are the role-level capabilities.
ROLE_CAPABILITIES = {
    Role.ADMIN: {
        "manage_users", "manage_roles", "view_all_engagements",
        "manage_engagements", "edit_testcases", "manage_findings",
        "review", "sign_off", "import_scans", "export_reports",
        "view_audit_log", "manage_catalog", "review_contributions",
    },
    Role.MANAGER: {
        "view_all_engagements", "manage_engagements", "edit_testcases",
        "manage_findings", "sign_off", "import_scans", "export_reports",
        "view_audit_log", "review_contributions",
    },
    Role.PENTESTER: {
        "edit_testcases", "manage_findings", "import_scans", "export_reports",
    },
    Role.REVIEWER: {
        "review", "export_reports",
    },
    Role.AUDITOR: {
        "view_all_engagements", "export_reports", "view_audit_log",
    },
}


class User(AbstractUser):
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.PENTESTER
    )
    title = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)

    class Meta:
        permissions = [
            ("view_audit_log", "Can view the audit log"),
        ]

    def has_capability(self, capability):
        """Role-level capability check (reach is checked separately)."""
        if self.is_superuser:
            return True
        return capability in ROLE_CAPABILITIES.get(self.role, set())

    @property
    def can_see_all_engagements(self):
        return self.has_capability("view_all_engagements")

    @property
    def is_read_only(self):
        return self.role == Role.AUDITOR

    def __str__(self):
        label = self.get_full_name() or self.username
        return f"{label} ({self.get_role_display()})"
