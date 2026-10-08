"""Assets: the concrete targets within an engagement, with type-specific data.

An engagement has many Assets (a web app, a /24, an AD domain, a Wi-Fi SSID,
a desktop binary, an ATM, …). Each Asset carries:
  - lightweight type-specific attributes (Asset.attributes JSON),
  - relational child records: Credentials (encrypted), Services, Files,
  - Functions (components of the asset that test cases attach to),
  - a Markdown walkthrough.
"""
from django.conf import settings
from django.db import models
from django.utils.text import slugify

from .constants import ASSET_TYPE_CHOICES
from .crypto import decrypt, encrypt


class Asset(models.Model):
    engagement = models.ForeignKey(
        "engagements.Engagement", on_delete=models.CASCADE, related_name="assets"
    )
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True)
    primary_target = models.CharField(
        max_length=255, blank=True,
        help_text="Main address/identifier (URL, IP, hostname, SSID).",
    )
    attributes = models.JSONField(default=dict, blank=True)
    walkthrough = models.TextField(blank=True, help_text="Markdown.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("asset_type", "name")
        unique_together = ("engagement", "slug")

    def __str__(self):
        return f"{self.name} ({self.get_asset_type_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "asset"
            slug = base
            i = 2
            qs = Asset.objects.filter(engagement=self.engagement)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=slug).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Credential(models.Model):
    class Kind(models.TextChoices):
        PASSWORD = "password", "Password"
        HASH = "hash", "Hash"
        TOKEN = "token", "Token / key"
        SSH_KEY = "ssh_key", "SSH key"
        OTHER = "other", "Other"

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="credentials"
    )
    label = models.CharField(max_length=160, help_text="e.g. 'admin web login', 'domain user'")
    username = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.PASSWORD)
    secret_encrypted = models.TextField(blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("label",)

    def __str__(self):
        return f"{self.label} ({self.username})"

    @property
    def secret(self):
        return decrypt(self.secret_encrypted)

    @secret.setter
    def secret(self, value):
        self.secret_encrypted = encrypt(value or "")


class Service(models.Model):
    """A network service on an asset (manual, or imported from a scan)."""

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="services")
    port = models.PositiveIntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=80, blank=True)
    product = models.CharField(max_length=160, blank=True)
    version = models.CharField(max_length=80, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("port",)

    def __str__(self):
        return f"{self.port}/{self.protocol} {self.name}".strip()


class FileArtifact(models.Model):
    """A file/binary associated with an asset (e.g. desktop app, config)."""

    class Kind(models.TextChoices):
        BINARY = "binary", "Binary"
        CONFIG = "config", "Config"
        LIBRARY = "library", "Library / DLL"
        INSTALLER = "installer", "Installer"
        OTHER = "other", "Other"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="files")
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.BINARY)
    path = models.CharField(max_length=500, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Function(models.Model):
    """A component/feature of an asset that test cases are grouped under.

    e.g. web: Login, Password reset, File upload; network: SMB, RDP.
    """

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="functions")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")
        unique_together = ("asset", "name")

    def __str__(self):
        return f"{self.asset.name} / {self.name}"
