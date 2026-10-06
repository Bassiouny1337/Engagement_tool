"""Nmap scan import: a Scan holds the uploaded XML's parsed hosts/ports/services."""
from django.conf import settings
from django.db import models


class Scan(models.Model):
    engagement = models.ForeignKey(
        "engagements.Engagement", on_delete=models.CASCADE, related_name="scans"
    )
    filename = models.CharField(max_length=255)
    args = models.CharField(max_length=500, blank=True)
    scanner = models.CharField(max_length=60, blank=True)
    version = models.CharField(max_length=60, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    # Parsed structure kept as JSON for flexible visualization (see parser).
    data = models.JSONField(default=dict, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.filename} ({self.engagement.code})"

    @property
    def hosts(self):
        return self.data.get("hosts", [])

    @property
    def host_count(self):
        return len(self.hosts)

    @property
    def up_count(self):
        return sum(1 for h in self.hosts if h.get("state") == "up")

    @property
    def open_port_count(self):
        n = 0
        for h in self.hosts:
            n += sum(1 for p in h.get("ports", []) if p.get("state") == "open")
        return n
