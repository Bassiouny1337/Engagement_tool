from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from apps.engagements.access import visible_engagements
from apps.engagements.models import Engagement
from apps.testcases.models import TestCase


@login_required
def home(request):
    engagements = visible_engagements(
        request.user, Engagement.objects.select_related("client")
    )
    counts = dict(
        engagements.values_list("status").annotate(n=Count("id"))
    )
    status_counts = [
        (label, counts.get(value, 0)) for value, label in Engagement.Status.choices
    ]
    tc = TestCase.objects.filter(engagement__in=engagements)
    tc_total = tc.count()
    tc_done = tc.filter(status__in=TestCase.DONE_STATUSES).count()

    context = {
        "user_role": request.user.get_role_display(),
        "engagement_count": engagements.count(),
        "status_counts": status_counts,
        "statuses": Engagement.Status.choices,
        "recent": engagements[:8],
        "tc_total": tc_total,
        "tc_done": tc_done,
        "tc_pct": round(100 * tc_done / tc_total) if tc_total else 0,
    }
    return render(request, "dashboard/home.html", context)
