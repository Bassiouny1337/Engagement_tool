"""Query helpers for findings."""
from django.db.models import Case, IntegerField, Value, When

from .models import Finding


def by_severity(queryset):
    """Order a Finding queryset most-severe first, then newest."""
    whens = [
        When(severity=sev, then=Value(rank))
        for sev, rank in Finding.SEVERITY_ORDER.items()
    ]
    return queryset.annotate(
        _rank=Case(*whens, default=Value(99), output_field=IntegerField())
    ).order_by("_rank", "-created_at")


def severity_counts(queryset):
    """Return {severity: count} for the queryset, with every severity present."""
    from django.db.models import Count

    counts = {sev: 0 for sev, _ in Finding.Severity.choices}
    for row in queryset.values("severity").annotate(n=Count("id")):
        counts[row["severity"]] = row["n"]
    return counts
