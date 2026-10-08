from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import escape
from django.views.decorators.http import require_POST

from apps.audit.models import AuditLog, record
from apps.engagements.access import can_access_engagement, can_edit_engagement_content
from apps.engagements.models import Engagement
from apps.notebook.render import render_markdown

from .constants import attribute_spec
from .forms import (
    AssetForm, AttributesForm, CredentialForm, FileArtifactForm,
    FunctionForm, ServiceForm, WalkthroughForm,
)
from .models import Asset, Credential, FileArtifact, Function, Service


def _eng_or_403(request, code):
    eng = get_object_or_404(Engagement, code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    return eng


def _asset_or_403(request, code, slug):
    eng = _eng_or_403(request, code)
    asset = get_object_or_404(Asset, engagement=eng, slug=slug)
    return eng, asset


def _require_edit(request, eng):
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot edit assets on this engagement.")


@login_required
def asset_list(request, code):
    eng = _eng_or_403(request, code)
    assets = eng.assets.all()
    atype = request.GET.get("type")
    if atype:
        assets = assets.filter(asset_type=atype)
    return render(request, "assets/list.html", {
        "eng": eng, "assets": assets, "active_type": atype,
        "can_edit": can_edit_engagement_content(request.user, eng),
    })


@login_required
def asset_create(request, code):
    eng = _eng_or_403(request, code)
    _require_edit(request, eng)
    form = AssetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        asset = form.save(commit=False)
        asset.engagement = eng
        asset.created_by = request.user
        asset.save()
        record(request.user, AuditLog.Action.CREATE,
               f"{eng.code} asset '{asset.name}' ({asset.asset_type})",
               target=asset, request=request)
        messages.success(request, "Asset created. Add its details below.")
        return redirect("assets:detail", code=eng.code, slug=asset.slug)
    return render(request, "assets/form.html", {"eng": eng, "form": form})


@login_required
def asset_detail(request, code, slug):
    eng, asset = _asset_or_403(request, code, slug)
    specs = attribute_spec(asset.asset_type)
    attr_rows = [(label, asset.attributes.get(key, "")) for key, label, _ in specs]
    tcs = asset.test_cases.all()
    done = sum(1 for t in tcs if t.is_done)
    return render(request, "assets/detail.html", {
        "eng": eng, "asset": asset, "attr_rows": attr_rows,
        "walkthrough_html": render_markdown(asset.walkthrough),
        "functions": asset.functions.all(),
        "services": asset.services.all(),
        "files": asset.files.all(),
        "credentials": asset.credentials.all(),
        "tc_total": tcs.count(), "tc_done": done,
        "forms": {
            "func": FunctionForm(), "svc": ServiceForm(),
            "file": FileArtifactForm(), "cred": CredentialForm(),
        },
        "can_edit": can_edit_engagement_content(request.user, eng),
    })


@login_required
def asset_edit(request, code, slug):
    eng, asset = _asset_or_403(request, code, slug)
    _require_edit(request, eng)
    form = AssetForm(request.POST or None, instance=asset)
    attrs = AttributesForm(request.POST or None, asset_type=asset.asset_type,
                           initial_attrs=asset.attributes)
    if request.method == "POST" and form.is_valid() and attrs.is_valid():
        asset = form.save(commit=False)
        asset.attributes = attrs.as_attributes()
        asset.save()
        record(request.user, AuditLog.Action.UPDATE,
               f"{eng.code} asset '{asset.name}' updated", target=asset, request=request)
        messages.success(request, "Asset updated.")
        return redirect("assets:detail", code=eng.code, slug=asset.slug)
    return render(request, "assets/edit.html", {
        "eng": eng, "asset": asset, "form": form, "attrs": attrs,
    })


@login_required
@require_POST
def asset_delete(request, code, slug):
    eng, asset = _asset_or_403(request, code, slug)
    _require_edit(request, eng)
    name = asset.name
    asset.delete()
    record(request.user, AuditLog.Action.DELETE,
           f"{eng.code} asset '{name}' deleted", request=request)
    messages.success(request, "Asset deleted.")
    return redirect("assets:list", code=eng.code)


@login_required
def walkthrough_edit(request, code, slug):
    eng, asset = _asset_or_403(request, code, slug)
    _require_edit(request, eng)
    form = WalkthroughForm(request.POST or None, instance=asset)
    if request.method == "POST" and form.is_valid():
        form.save()
        record(request.user, AuditLog.Action.UPDATE,
               f"{eng.code} asset '{asset.name}' walkthrough", target=asset, request=request)
        messages.success(request, "Walkthrough saved.")
        return redirect("assets:detail", code=eng.code, slug=asset.slug)
    return render(request, "assets/walkthrough.html", {"eng": eng, "asset": asset, "form": form})


# ---- child records (all require edit) ----

def _add_child(request, code, slug, form_cls, label):
    eng, asset = _asset_or_403(request, code, slug)
    _require_edit(request, eng)
    form = form_cls(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.asset = asset
        if hasattr(obj, "created_by"):
            obj.created_by = request.user
        obj.save()
        record(request.user, AuditLog.Action.CREATE,
               f"{eng.code} {label} on asset '{asset.name}'", target=asset, request=request)
        messages.success(request, f"{label.capitalize()} added.")
    else:
        messages.error(request, f"Could not add {label}: {form.errors.as_text()}")
    return redirect("assets:detail", code=eng.code, slug=asset.slug)


@login_required
@require_POST
def add_function(request, code, slug):
    return _add_child(request, code, slug, FunctionForm, "function")


@login_required
@require_POST
def add_service(request, code, slug):
    return _add_child(request, code, slug, ServiceForm, "service")


@login_required
@require_POST
def add_file(request, code, slug):
    return _add_child(request, code, slug, FileArtifactForm, "file")


@login_required
@require_POST
def add_credential(request, code, slug):
    return _add_child(request, code, slug, CredentialForm, "credential")


@login_required
@require_POST
def delete_child(request, code, slug, model, pk):
    eng, asset = _asset_or_403(request, code, slug)
    _require_edit(request, eng)
    mapping = {"function": Function, "service": Service,
               "file": FileArtifact, "credential": Credential}
    model_cls = mapping.get(model)
    if model_cls:
        model_cls.objects.filter(pk=pk, asset=asset).delete()
        messages.success(request, f"{model.capitalize()} removed.")
    return redirect("assets:detail", code=eng.code, slug=asset.slug)


@login_required
@require_POST
def reveal_credential(request, code, slug, pk):
    """Return a credential secret (HTMX). Members only; every reveal is logged."""
    eng, asset = _asset_or_403(request, code, slug)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied()
    cred = get_object_or_404(Credential, pk=pk, asset=asset)
    record(request.user, AuditLog.Action.UPDATE,
           f"{eng.code} revealed credential '{cred.label}' on '{asset.name}'",
           target=cred, request=request,
           metadata={"action": "credential_reveal"})
    secret = cred.secret or "(empty)"
    return HttpResponse(f'<code class="mono">{escape(secret)}</code>')
