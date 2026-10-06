from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import require_capability
from apps.audit.models import AuditLog, record
from apps.testcases.progress import engagement_progress

from .access import can_access_engagement, visible_engagements
from .forms import AddDomainForm, EngagementForm, ScopeItemForm
from .models import Engagement, EngagementDomain, ScopeItem


@login_required
def engagement_list(request):
    engagements = visible_engagements(
        request.user, Engagement.objects.select_related("client")
    )
    status = request.GET.get("status")
    if status:
        engagements = engagements.filter(status=status)
    return render(request, "engagements/list.html", {
        "engagements": engagements,
        "statuses": Engagement.Status.choices,
        "active_status": status,
    })


@login_required
@require_capability("manage_engagements")
def engagement_create(request):
    form = EngagementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        eng = form.save(commit=False)
        eng.created_by = request.user
        eng.save()
        record(request.user, AuditLog.Action.CREATE,
               f"Created engagement {eng.code}", target=eng, request=request)
        messages.success(request, f"Engagement {eng.code} created.")
        return redirect("engagements:detail", code=eng.code)
    return render(request, "engagements/form.html", {"form": form, "mode": "create"})


def _get_visible_or_403(request, code):
    eng = get_object_or_404(Engagement.objects.select_related("client"), code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    return eng


@login_required
def engagement_detail(request, code):
    eng = _get_visible_or_403(request, code)
    progress = engagement_progress(eng)
    return render(request, "engagements/detail.html", {
        "eng": eng,
        "progress": progress,
        "scope_items": eng.scope_items.all(),
        "team": eng.team_assignments.select_related("user"),
        "add_domain_form": AddDomainForm(),
        "scope_form": ScopeItemForm(),
        "transitions": list(eng.TRANSITIONS.get(eng.status, set())),
    })


@login_required
@require_capability("manage_engagements")
def add_domain(request, code):
    eng = _get_visible_or_403(request, code)
    form = AddDomainForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        key = form.cleaned_data["domain_key"]
        obj, created = EngagementDomain.objects.get_or_create(
            engagement=eng, domain_key=key
        )
        if created:
            record(request.user, AuditLog.Action.UPDATE,
                   f"Added domain {key} to {eng.code}", target=eng, request=request)
            messages.success(request, f"Domain added and checklist seeded.")
        else:
            messages.info(request, "Domain already in scope.")
    return redirect("engagements:detail", code=eng.code)


@login_required
@require_capability("manage_engagements")
def change_status(request, code):
    eng = _get_visible_or_403(request, code)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if not eng.can_transition_to(new_status):
            messages.error(request, f"Cannot move from {eng.get_status_display()} to that state.")
        else:
            old = eng.status
            eng.status = new_status
            eng.save(update_fields=["status", "updated_at"])
            record(request.user, AuditLog.Action.UPDATE,
                   f"{eng.code} status {old} -> {new_status}", target=eng, request=request)
            messages.success(request, f"Status updated to {eng.get_status_display()}.")
    return redirect("engagements:detail", code=eng.code)


@login_required
@require_capability("manage_engagements")
def add_scope_item(request, code):
    eng = _get_visible_or_403(request, code)
    form = ScopeItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.engagement = eng
        item.save()
        record(request.user, AuditLog.Action.CREATE,
               f"Added scope item {item.value} to {eng.code}", target=eng, request=request)
        messages.success(request, "Scope item added.")
    return redirect("engagements:detail", code=eng.code)


@login_required
@require_capability("manage_engagements")
def remove_scope_item(request, code, pk):
    eng = _get_visible_or_403(request, code)
    if request.method == "POST":
        ScopeItem.objects.filter(pk=pk, engagement=eng).delete()
        messages.success(request, "Scope item removed.")
    return redirect("engagements:detail", code=eng.code)
