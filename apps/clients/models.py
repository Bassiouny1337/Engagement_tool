from django.db import models


class ClientOrg(models.Model):
    """A customer organization that engagements are performed for."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    primary_contact_name = models.CharField(max_length=160, blank=True)
    primary_contact_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "client organization"

    def __str__(self):
        return self.name
