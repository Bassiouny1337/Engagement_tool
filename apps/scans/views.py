import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import require_capability
from apps.audit.models import AuditLog, record
from apps.engagements.access import can_access_engagement, can_edit_engagement_content
from apps.engagements.models import Engagement, EngagementDomain, ScopeItem
from apps.testcases.models import TestCase

from .forms import ScanUploadForm
from .graph import build_elements
from .models import Scan
from .parser import NmapParseError, parse_nmap_xml

MAX_BYTES = 25 * 1024 * 1024


def _engagement_or_403(request, code):
    eng = get_object_or_404(Engagement, code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    return eng


@login_required
def scan_list(request, code):
    eng = _engagement_or_403(request, code)
    return render(request, "scans/list.html", {
        "eng": eng, "scans": eng.scans.select_related("uploaded_by"),
        "can_import": (request.user.has_capability("import_scans")
                       and can_edit_engagement_content(request.user, eng)),
    })


@login_required
@require_capability("import_scans")
def scan_upload(request, code):
    eng = _engagement_or_403(request, code)
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    form = ScanUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        f = form.cleaned_data["file"]
        if f.size > MAX_BYTES:
            messages.error(request, "File exceeds the 25 MB limit.")
            return redirect("scans:upload", code=eng.code)
        try:
            parsed = parse_nmap_xml(f.read())
        except NmapParseError as exc:
            messages.error(request, f"Could not import: {exc}")
            return redirect("scans:upload", code=eng.code)

        scan = Scan.objects.create(
            engagement=eng,
            filename=f.name[:255],
            scanner=parsed["meta"].get("scanner", ""),
            args=parsed["meta"].get("args", "")[:500],
            version=parsed["meta"].get("version", ""),
            data=parsed,
            uploaded_by=request.user,
        )
        # A network scan implies the network domain is in scope.
        EngagementDomain.objects.get_or_create(engagement=eng, domain_key="network")
        record(request.user, AuditLog.Action.IMPORT,
               f"Imported nmap scan {scan.filename} ({scan.host_count} hosts)",
               target=scan, request=request)
        messages.success(
            request,
            f"Imported {scan.host_count} hosts, {scan.open_port_count} open ports.")
        return redirect("scans:detail", code=eng.code, pk=scan.pk)

    return render(request, "scans/upload.html", {"eng": eng, "form": form})


@login_required
def scan_detail(request, code, pk):
    eng = _engagement_or_403(request, code)
    scan = get_object_or_404(Scan, pk=pk, engagement=eng)
    return render(request, "scans/detail.html", {
        "eng": eng, "scan": scan,
        "elements_json": json.dumps(build_elements(scan)),
        "can_edit": (request.user.has_capability("edit_testcases")
                     and can_edit_engagement_content(request.user, eng)),
        "can_scope": (request.user.has_capability("manage_engagements")
                      and can_access_engagement(request.user, eng)),
    })


@login_required
@require_POST
def add_scope_from_host(request, code, pk):
    eng = _engagement_or_403(request, code)
    if not request.user.has_capability("manage_engagements"):
        raise PermissionDenied("Your role cannot manage scope.")
    scan = get_object_or_404(Scan, pk=pk, engagement=eng)
    ip = request.POST.get("ip", "").strip()
    if not ip:
        messages.error(request, "No host specified.")
        return redirect("scans:detail", code=eng.code, pk=scan.pk)
    obj, created = ScopeItem.objects.get_or_create(
        engagement=eng, value=ip,
        defaults={"domain_key": "network", "kind": ScopeItem.Kind.IP,
                  "notes": f"From scan {scan.filename}"},
    )
    messages.success(request, f"{'Added' if created else 'Already in'} scope: {ip}")
    return redirect("scans:detail", code=eng.code, pk=scan.pk)


@login_required
@require_POST
def add_testcase_from_service(request, code, pk):
    eng = _engagement_or_403(request, code)
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot add test cases.")
    scan = get_object_or_404(Scan, pk=pk, engagement=eng)
    ip = request.POST.get("ip", "").strip()
    port = request.POST.get("port", "").strip()
    service = request.POST.get("service", "").strip() or "service"
    if not ip or not port:
        messages.error(request, "Host and port are required.")
        return redirect("scans:detail", code=eng.code, pk=scan.pk)
    EngagementDomain.objects.get_or_create(engagement=eng, domain_key="network")
    tc = TestCase.objects.create(
        engagement=eng, domain_key="network", category="From scan",
        title=f"Review {service} on {ip}:{port}", is_custom=True,
        notes=f"Discovered open in scan {scan.filename}.", updated_by=request.user,
    )
    record(request.user, AuditLog.Action.CREATE,
           f"{eng.code} scan-derived testcase {ip}:{port}", target=tc, request=request)
    messages.success(request, f"Added test case for {ip}:{port}.")
    return redirect("scans:detail", code=eng.code, pk=scan.pk)
