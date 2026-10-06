from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.permissions import require_capability
from apps.audit.models import AuditLog, record
from apps.engagements.access import can_access_engagement, can_edit_engagement_content
from apps.engagements.models import Engagement
from apps.testcases.models import TestCase

from .forms import FindingForm
from .models import Finding
from .query import by_severity, severity_counts


def _engagement_or_403(request, code):
    eng = get_object_or_404(Engagement, code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    return eng


def _require_edit(request, eng):
    if not request.user.has_capability("manage_findings") or not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot manage findings on this engagement.")


@login_required
def finding_list(request, code):
    eng = _engagement_or_403(request, code)
    findings = by_severity(eng.findings.select_related("source_test_case", "created_by"))
    sev = request.GET.get("severity")
    if sev:
        findings = findings.filter(severity=sev)
    counts = severity_counts(eng.findings.all())
    severity_chips = [(v, label, counts.get(v, 0)) for v, label in Finding.Severity.choices]
    return render(request, "findings/list.html", {
        "eng": eng, "findings": findings,
        "severity_chips": severity_chips,
        "active_severity": sev,
        "can_edit": (request.user.has_capability("manage_findings")
                     and can_edit_engagement_content(request.user, eng)),
        "can_review": request.user.has_capability("review"),
    })


@login_required
def finding_detail(request, code, pk):
    eng = _engagement_or_403(request, code)
    finding = get_object_or_404(Finding, pk=pk, engagement=eng)
    return render(request, "findings/detail.html", {
        "eng": eng, "f": finding,
        "can_edit": (request.user.has_capability("manage_findings")
                     and can_edit_engagement_content(request.user, eng)),
        "can_review": request.user.has_capability("review"),
    })


@login_required
def finding_edit(request, code, pk=None):
    eng = _engagement_or_403(request, code)
    _require_edit(request, eng)
    instance = get_object_or_404(Finding, pk=pk, engagement=eng) if pk else None

    initial = {}
    tc = None
    if not instance:
        tc_id = request.GET.get("from_testcase")
        if tc_id:
            tc = get_object_or_404(TestCase, pk=tc_id, engagement=eng)
            initial = {
                "title": tc.title,
                "domain_key": tc.domain_key,
                "description": tc.notes,
            }

    form = FindingForm(request.POST or None, instance=instance, initial=initial)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.engagement = eng
        if not obj.pk:
            obj.created_by = request.user
            if tc:
                obj.source_test_case = tc
        obj.save()
        record(request.user,
               AuditLog.Action.UPDATE if pk else AuditLog.Action.CREATE,
               f"{eng.code} finding '{obj.title}' ({obj.severity})",
               target=obj, request=request)
        messages.success(request, "Finding saved.")
        return redirect("findings:detail", code=eng.code, pk=obj.pk)

    return render(request, "findings/form.html",
                  {"eng": eng, "form": form, "instance": instance, "from_tc": tc})


@login_required
@require_POST
def finding_review(request, code, pk):
    eng = _engagement_or_403(request, code)
    if not request.user.has_capability("review"):
        raise PermissionDenied("Your role cannot review findings.")
    finding = get_object_or_404(Finding, pk=pk, engagement=eng)
    finding.reviewed_by = request.user
    finding.reviewed_at = timezone.now()
    finding.save(update_fields=["reviewed_by", "reviewed_at", "updated_at"])
    record(request.user, AuditLog.Action.SIGN_OFF,
           f"{eng.code} finding '{finding.title}' reviewed", target=finding, request=request)
    messages.success(request, "Finding marked reviewed.")
    return redirect("findings:detail", code=eng.code, pk=finding.pk)
