"""Append-only audit log.

Records who did what, when, against which object. Rows are never updated or
deleted through the app; the admin is registered read-only.
"""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        IMPORT = "import", "Import"
        EXPORT = "export", "Export"
        SIGN_OFF = "sign_off", "Sign-off"

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=50, blank=True)
    summary = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        who = self.actor or "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {who} {self.action} {self.summary}"


def record(actor, action, summary, target=None, metadata=None, request=None):
    """Convenience helper to write an audit entry from anywhere."""
    entry = AuditLog(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        summary=summary[:255],
        metadata=metadata or {},
    )
    if target is not None:
        entry.target_type = target.__class__.__name__
        entry.target_id = str(getattr(target, "pk", ""))
    if request is not None:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        entry.ip_address = (
            xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
        )
    entry.save()
    return entry
