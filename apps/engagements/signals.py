from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EngagementDomain


@receiver(post_save, sender=EngagementDomain)
def seed_testcases_for_domain(sender, instance, created, **kwargs):
    """When a domain is added to an engagement, seed its checklist."""
    if not created:
        return
    # Imported lazily to avoid an app-loading cycle.
    from apps.testcases.models import seed_engagement_domain

    seed_engagement_domain(instance.engagement, instance.domain_key)
