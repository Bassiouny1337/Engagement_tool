from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.audit.models import AuditLog, record
from apps.engagements.access import can_access_engagement, can_edit_engagement_content
from apps.engagements.models import Engagement

from .models import TestCase, import_scenario


def _engagement_or_403(request, code):
    eng = get_object_or_404(Engagement, code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    return eng


@login_required
def board(request, code):
    eng = _engagement_or_403(request, code)
    qs = eng.test_cases.select_related("assignee", "asset", "function")

    asset_slug = request.GET.get("asset")
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    active_asset = None
    if asset_slug:
        active_asset = eng.assets.filter(slug=asset_slug).first()
        qs = qs.filter(asset=active_asset) if active_asset else qs.none()

    # When an asset is selected, group by Function (then category). Otherwise
    # group by Asset (then category), with an "Unassigned" bucket for null.
    grouped = defaultdict(lambda: defaultdict(list))
    for tc in qs:
        if active_asset:
            outer = tc.function.name if tc.function else "General"
        else:
            outer = tc.asset.name if tc.asset else "General (no asset)"
        grouped[outer][tc.category].append(tc)
    grouped = {k: dict(v) for k, v in grouped.items()}

    return render(request, "testcases/board.html", {
        "eng": eng,
        "grouped": grouped,
        "statuses": TestCase.Status.choices,
        "assets": eng.assets.all(),
        "active_asset": active_asset,
        "functions": active_asset.functions.all() if active_asset else [],
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


@login_required
@require_POST
def update_notes(request, code, pk):
    eng = _engagement_or_403(request, code)
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot edit test cases on this engagement.")
    tc = get_object_or_404(TestCase, pk=pk, engagement=eng)
    tc.notes = request.POST.get("notes", "")
    tc.updated_by = request.user
    tc.save(update_fields=["notes", "updated_by", "updated_at"])
    record(request.user, AuditLog.Action.UPDATE,
           f"{eng.code} testcase #{tc.pk} notes updated", target=tc, request=request)
    if request.headers.get("HX-Request"):
        from django.http import HttpResponse
        return HttpResponse("Saved ✓")
    return redirect("testcases:board", code=eng.code)


@login_required
@require_POST
def add_custom(request, code):
    eng = _engagement_or_403(request, code)
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot edit test cases on this engagement.")
    title = request.POST.get("title", "").strip()
    category = request.POST.get("category", "").strip() or "Custom"
    asset_slug = request.POST.get("asset", "").strip()
    function_id = request.POST.get("function", "").strip()

    asset = eng.assets.filter(slug=asset_slug).first() if asset_slug else None
    function = None
    if asset and function_id.isdigit():
        function = asset.functions.filter(pk=int(function_id)).first()

    # Domain comes from the chosen asset; otherwise require an in-scope domain.
    if asset:
        domain_key = asset.asset_type
    else:
        domain_key = request.POST.get("domain_key", "").strip()
        if domain_key not in eng.domain_keys:
            return HttpResponseBadRequest("title and a valid in-scope domain are required")
    if not title:
        return HttpResponseBadRequest("title is required")

    tc = TestCase.objects.create(
        engagement=eng, domain_key=domain_key, category=category,
        title=title, is_custom=True, asset=asset, function=function,
        updated_by=request.user,
    )
    record(request.user, AuditLog.Action.CREATE,
           f"{eng.code} custom testcase '{title}'", target=tc, request=request)
    messages.success(request, "Custom test case added.")
    target = redirect("testcases:board", code=eng.code)
    if asset:
        target["Location"] += f"?asset={asset.slug}"
    return target


@login_required
def scenario_library(request, code):
    """Browse the scenario library (filtered to the engagement's domains)."""
    from apps.catalog.models import Scenario

    eng = _engagement_or_403(request, code)
    scenarios = Scenario.objects.filter(is_active=True, domain_key__in=eng.domain_keys)
    domain = request.GET.get("domain")
    q = request.GET.get("q", "").strip()
    if domain:
        scenarios = scenarios.filter(domain_key=domain)
    if q:
        scenarios = scenarios.filter(title__icontains=q)
    return render(request, "testcases/scenario_library.html", {
        "eng": eng, "scenarios": scenarios, "domain_keys": eng.domain_keys,
        "active_domain": domain, "q": q,
        "can_edit": can_edit_engagement_content(request.user, eng),
    })


@login_required
@require_POST
def pull_scenario(request, code, scenario_id):
    from apps.catalog.models import Scenario

    eng = _engagement_or_403(request, code)
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot edit test cases on this engagement.")
    scenario = get_object_or_404(Scenario, pk=scenario_id, is_active=True)
    if scenario.domain_key not in eng.domain_keys:
        return HttpResponseBadRequest("scenario domain is not in this engagement's scope")
    tc = import_scenario(eng, scenario, created_by=request.user)
    record(request.user, AuditLog.Action.IMPORT,
           f"{eng.code} pulled scenario '{scenario.title}'", target=tc, request=request)
    messages.success(request, f"Added “{scenario.title}” to the engagement.")
    return redirect("testcases:board", code=eng.code)
