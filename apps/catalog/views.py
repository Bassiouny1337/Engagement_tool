from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import require_capability
from apps.audit.models import AuditLog, record
from apps.domains.constants import DOMAIN_CHOICES

from .forms import ChecklistItemForm, ScenarioForm
from .models import ChecklistItem, Scenario

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
    items = ChecklistItem.objects.all()
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
    scenarios = Scenario.objects.all()
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
