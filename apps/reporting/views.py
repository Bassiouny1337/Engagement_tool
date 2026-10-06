from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.audit.models import AuditLog, record
from apps.engagements.access import can_access_engagement
from apps.engagements.models import Engagement

from .report import build_markdown


def _engagement_or_403(request, code):
    eng = get_object_or_404(Engagement, code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    if not request.user.has_capability("export_reports"):
        raise PermissionDenied("Your role cannot export reports.")
    return eng


@login_required
def report_preview(request, code):
    eng = _engagement_or_403(request, code)
    return render(request, "reporting/preview.html",
                  {"eng": eng, "markdown": build_markdown(eng)})


@login_required
def report_download(request, code):
    eng = _engagement_or_403(request, code)
    md = build_markdown(eng)
    record(request.user, AuditLog.Action.EXPORT,
           f"Exported report for {eng.code}", target=eng, request=request)
    resp = HttpResponse(md, content_type="text/markdown; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{eng.code}-report.md"'
    return resp
