from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.audit.models import AuditLog, record
from apps.engagements.access import can_access_engagement, can_edit_engagement_content
from apps.engagements.models import Engagement

from .models import TestCase


def _engagement_or_403(request, code):
    eng = get_object_or_404(Engagement, code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    return eng


@login_required
def board(request, code):
    eng = _engagement_or_403(request, code)
    qs = eng.test_cases.select_related("assignee")

    domain = request.GET.get("domain")
    status = request.GET.get("status")
    if domain:
        qs = qs.filter(domain_key=domain)
    if status:
        qs = qs.filter(status=status)

    grouped = defaultdict(lambda: defaultdict(list))
    for tc in qs:
        grouped[tc.get_domain_key_display()][tc.category].append(tc)
    # Plain nested dict for the template.
    grouped = {d: dict(cats) for d, cats in grouped.items()}

    return render(request, "testcases/board.html", {
        "eng": eng,
        "grouped": grouped,
        "statuses": TestCase.Status.choices,
        "domain_keys": eng.domain_keys,
        "active_domain": domain,
        "active_status": status,
        "can_edit": can_edit_engagement_content(request.user, eng),
    })


@login_required
@require_POST
def update_status(request, code, pk):
    eng = _engagement_or_403(request, code)
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot edit test cases on this engagement.")
    tc = get_object_or_404(TestCase, pk=pk, engagement=eng)
    new_status = request.POST.get("status")
    valid = {s for s, _ in TestCase.Status.choices}
    if new_status not in valid:
        return HttpResponseBadRequest("invalid status")
    tc.status = new_status
    tc.updated_by = request.user
    tc.save(update_fields=["status", "updated_by", "updated_at"])
    record(request.user, AuditLog.Action.UPDATE,
           f"{eng.code} testcase #{tc.pk} -> {new_status}", target=tc, request=request)

    if request.headers.get("HX-Request"):
        return render(request, "testcases/_row.html",
                      {"tc": tc, "eng": eng, "statuses": TestCase.Status.choices,
                       "can_edit": True})
    return redirect("testcases:board", code=eng.code)
