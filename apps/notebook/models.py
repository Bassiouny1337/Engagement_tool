"""Per-engagement notebook: nested Markdown wiki pages."""
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    engagement = models.ForeignKey(
        "engagements.Engagement", on_delete=models.CASCADE, related_name="pages"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    content = models.TextField(blank=True, help_text="Markdown.")
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "title")
        unique_together = ("engagement", "slug")
        indexes = [models.Index(fields=["engagement", "parent"])]

    def __str__(self):
        return f"{self.engagement.code}:{self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.title) or "page"
        slug = base
        i = 2
        qs = Page.objects.filter(engagement=self.engagement)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    def ancestors(self):
        """Return this page's ancestors, root first (for breadcrumbs)."""
        chain = []
        node = self.parent
        seen = set()
        while node and node.pk not in seen:
            seen.add(node.pk)
            chain.append(node)
            node = node.parent
        return list(reversed(chain))
