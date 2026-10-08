from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.permissions import require_capability
from apps.audit.models import AuditLog, record
from apps.domains.constants import DOMAIN_CHOICES

from .forms import ChecklistItemForm, ScenarioForm
from .models import ChecklistItem, ContributionRequest, Scenario

CATALOG_CAP = "manage_catalog"


@login_required
@require_capability(CATALOG_CAP)
def catalog_home(request):
    return render(request, "catalog/home.html", {
        "checklist_count": ChecklistItem.objects.count(),
        "scenario_count": Scenario.objects.count(),
        "domains": DOMAIN_CHOICES,
    })


# ---- Checklist items ----

@login_required
@require_capability(CATALOG_CAP)
def checklist_list(request):
    items = ChecklistItem.objects.filter(owner__isnull=True)  # global only
    domain = request.GET.get("domain")
    if domain:
        items = items.filter(domain_key=domain)
    return render(request, "catalog/checklist_list.html", {
        "items": items, "domains": DOMAIN_CHOICES, "active_domain": domain,
    })


@login_required
@require_capability(CATALOG_CAP)
def checklist_edit(request, pk=None):
    instance = get_object_or_404(ChecklistItem, pk=pk) if pk else None
    form = ChecklistItemForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if not obj.pk:
            obj.created_by = request.user
        obj.save()
        record(request.user,
               AuditLog.Action.UPDATE if pk else AuditLog.Action.CREATE,
               f"{'Updated' if pk else 'Created'} checklist item {obj.title}",
               target=obj, request=request)
        messages.success(request, "Checklist item saved.")
        return redirect("catalog:checklist_list")
    return render(request, "catalog/checklist_form.html",
                  {"form": form, "instance": instance})


@login_required
@require_capability(CATALOG_CAP)
def checklist_delete(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk)
    if request.method == "POST":
        title = item.title
        item.delete()
        record(request.user, AuditLog.Action.DELETE,
               f"Deleted checklist item {title}", request=request)
        messages.success(request, "Checklist item deleted.")
    return redirect("catalog:checklist_list")


# ---- Scenarios ----

@login_required
@require_capability(CATALOG_CAP)
def scenario_list(request):
    scenarios = Scenario.objects.filter(owner__isnull=True)  # global only
    domain = request.GET.get("domain")
    q = request.GET.get("q", "").strip()
    if domain:
        scenarios = scenarios.filter(domain_key=domain)
    if q:
        scenarios = scenarios.filter(title__icontains=q)
    return render(request, "catalog/scenario_list.html", {
        "scenarios": scenarios, "domains": DOMAIN_CHOICES,
        "active_domain": domain, "q": q,
    })


@login_required
@require_capability(CATALOG_CAP)
def scenario_edit(request, pk=None):
    instance = get_object_or_404(Scenario, pk=pk) if pk else None
    form = ScenarioForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if not obj.pk:
            obj.created_by = request.user
        obj.save()
        record(request.user,
               AuditLog.Action.UPDATE if pk else AuditLog.Action.CREATE,
               f"{'Updated' if pk else 'Created'} scenario {obj.title}",
               target=obj, request=request)
        messages.success(request, "Scenario saved.")
        return redirect("catalog:scenario_list")
    return render(request, "catalog/scenario_form.html",
                  {"form": form, "instance": instance})


@login_required
@require_capability(CATALOG_CAP)
def scenario_delete(request, pk):
    s = get_object_or_404(Scenario, pk=pk)
    if request.method == "POST":
        title = s.title
        s.delete()
        record(request.user, AuditLog.Action.DELETE,
               f"Deleted scenario {title}", request=request)
        messages.success(request, "Scenario deleted.")
    return redirect("catalog:scenario_list")


# ---- Personal catalog (any user who can edit test content) ----

PERSONAL_CAP = "edit_testcases"
REVIEW_CAP = "review_contributions"


@login_required
@require_capability(PERSONAL_CAP)
def my_catalog(request):
    return render(request, "catalog/mine.html", {
        "checklist_items": ChecklistItem.objects.filter(owner=request.user),
        "scenarios": Scenario.objects.filter(owner=request.user),
        "my_requests": ContributionRequest.objects.filter(requested_by=request.user)[:20],
    })


@login_required
@require_capability(PERSONAL_CAP)
def my_checklist_edit(request, pk=None):
    instance = get_object_or_404(ChecklistItem, pk=pk, owner=request.user) if pk else None
    form = ChecklistItemForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.owner = request.user
        if not obj.pk:
            obj.created_by = request.user
        obj.save()
        messages.success(request, "Personal checklist item saved.")
        return redirect("catalog:mine")
    return render(request, "catalog/checklist_form.html",
                  {"form": form, "instance": instance, "personal": True})


@login_required
@require_capability(PERSONAL_CAP)
def my_scenario_edit(request, pk=None):
    instance = get_object_or_404(Scenario, pk=pk, owner=request.user) if pk else None
    form = ScenarioForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.owner = request.user
        if not obj.pk:
            obj.created_by = request.user
        obj.save()
        messages.success(request, "Personal scenario saved.")
        return redirect("catalog:mine")
    return render(request, "catalog/scenario_form.html",
                  {"form": form, "instance": instance, "personal": True})


@login_required
@require_capability(PERSONAL_CAP)
@require_POST
def my_item_delete(request, kind, pk):
    model = ChecklistItem if kind == "checklist" else Scenario
    model.objects.filter(pk=pk, owner=request.user).delete()
    messages.success(request, "Deleted.")
    return redirect("catalog:mine")


@login_required
@require_capability(PERSONAL_CAP)
@require_POST
def request_promotion(request, kind, pk):
    """Submit a request to promote a personal item into the global catalog."""
    if kind == "checklist":
        item = get_object_or_404(ChecklistItem, pk=pk, owner=request.user)
        if item.contribution_requests.filter(status="pending").exists():
            messages.info(request, "A request for this item is already pending.")
            return redirect("catalog:mine")
        ContributionRequest.objects.create(
            kind=ContributionRequest.Kind.CHECKLIST, checklist_item=item,
            requested_by=request.user, note=request.POST.get("note", "")[:255])
    else:
        item = get_object_or_404(Scenario, pk=pk, owner=request.user)
        if item.contribution_requests.filter(status="pending").exists():
            messages.info(request, "A request for this item is already pending.")
            return redirect("catalog:mine")
        ContributionRequest.objects.create(
            kind=ContributionRequest.Kind.SCENARIO, scenario=item,
            requested_by=request.user, note=request.POST.get("note", "")[:255])
    record(request.user, AuditLog.Action.CREATE,
           f"Requested promotion of {kind} '{item}'", request=request)
    messages.success(request, "Promotion requested — an admin/manager will review it.")
    return redirect("catalog:mine")


# ---- Contribution review queue (admin / manager) ----

@login_required
@require_capability(REVIEW_CAP)
def contribution_list(request):
    status = request.GET.get("status", "pending")
    reqs = ContributionRequest.objects.select_related(
        "requested_by", "checklist_item", "scenario")
    if status in ("pending", "approved", "rejected"):
        reqs = reqs.filter(status=status)
    return render(request, "catalog/contributions.html",
                  {"requests": reqs, "active_status": status})


@login_required
@require_capability(REVIEW_CAP)
@require_POST
def contribution_approve(request, pk):
    req = get_object_or_404(ContributionRequest, pk=pk)
    promoted = req.approve(request.user)
    if promoted is not None:
        record(request.user, AuditLog.Action.UPDATE,
               f"Approved contribution #{req.pk} -> global catalog",
               target=promoted, request=request)
        messages.success(request, "Approved — now available to all pentesters.")
    else:
        messages.info(request, "Already decided.")
    return redirect("catalog:contributions")


@login_required
@require_capability(REVIEW_CAP)
@require_POST
def contribution_reject(request, pk):
    req = get_object_or_404(ContributionRequest, pk=pk)
    req.reject(request.user, note=request.POST.get("note", ""))
    record(request.user, AuditLog.Action.UPDATE,
           f"Rejected contribution #{req.pk}", request=request)
    messages.success(request, "Request rejected.")
    return redirect("catalog:contributions")
