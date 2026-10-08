from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.audit.models import AuditLog, record
from apps.engagements.access import can_access_engagement, can_edit_engagement_content
from apps.engagements.models import Engagement

from .forms import PageForm
from .models import Page
from .render import render_markdown


def _engagement_or_403(request, code):
    eng = get_object_or_404(Engagement, code=code)
    if not can_access_engagement(request.user, eng):
        raise PermissionDenied("You are not assigned to this engagement.")
    return eng


def _require_edit(request, eng):
    if not can_edit_engagement_content(request.user, eng):
        raise PermissionDenied("Your role cannot edit the notebook on this engagement.")


def _tree(eng):
    """Build a nested page tree [(page, [children...]), ...]."""
    pages = list(eng.pages.all())
    by_parent = {}
    for p in pages:
        by_parent.setdefault(p.parent_id, []).append(p)

    def build(parent_id):
        return [(p, build(p.id)) for p in by_parent.get(parent_id, [])]

    return build(None)


def _descendant_ids(page):
    ids = set()
    stack = list(page.children.all())
    while stack:
        node = stack.pop()
        ids.add(node.id)
        stack.extend(node.children.all())
    return ids


@login_required
def notebook_home(request, code):
    eng = _engagement_or_403(request, code)
    first = eng.pages.first()
    if first:
        return redirect("notebook:page", code=eng.code, slug=first.slug)
    return render(request, "notebook/page.html", {
        "eng": eng, "tree": _tree(eng), "page": None,
        "can_edit": can_edit_engagement_content(request.user, eng),
    })


@login_required
def page_view(request, code, slug):
    eng = _engagement_or_403(request, code)
    page = get_object_or_404(Page, engagement=eng, slug=slug)
    return render(request, "notebook/page.html", {
        "eng": eng, "tree": _tree(eng), "page": page,
        "html": render_markdown(page.content),
        "can_edit": can_edit_engagement_content(request.user, eng),
    })


@login_required
def page_edit(request, code, slug=None):
    eng = _engagement_or_403(request, code)
    _require_edit(request, eng)
    instance = get_object_or_404(Page, engagement=eng, slug=slug) if slug else None

    form = PageForm(request.POST or None, instance=instance, engagement=eng)
    if instance:
        bad = _descendant_ids(instance) | {instance.id}
        form.fields["parent"].queryset = eng.pages.exclude(id__in=bad)

    if request.method == "POST" and form.is_valid():
        page = form.save(commit=False)
        page.engagement = eng
        if not page.pk:
            page.created_by = request.user
        page.updated_by = request.user
        page.save()
        record(request.user,
               AuditLog.Action.UPDATE if slug else AuditLog.Action.CREATE,
               f"{eng.code} notebook page '{page.title}'", target=page, request=request)
        messages.success(request, "Page saved.")
        return redirect("notebook:page", code=eng.code, slug=page.slug)

    return render(request, "notebook/edit.html", {
        "eng": eng, "form": form, "instance": instance,
    })


@login_required
@require_POST
def page_delete(request, code, slug):
    eng = _engagement_or_403(request, code)
    _require_edit(request, eng)
    page = get_object_or_404(Page, engagement=eng, slug=slug)
    title = page.title
    page.delete()  # cascades to children
    record(request.user, AuditLog.Action.DELETE,
           f"{eng.code} notebook page '{title}' deleted", request=request)
    messages.success(request, "Page (and any sub-pages) deleted.")
    return redirect("notebook:home", code=eng.code)


@login_required
@require_POST
def preview(request, code):
    """Live Markdown preview (HTMX). Renders sanitized HTML from posted text."""
    eng = _engagement_or_403(request, code)
    text = request.POST.get("content") or request.POST.get("walkthrough") or ""
    html = render_markdown(text)
    return HttpResponse(html or '<p class="muted">Nothing to preview.</p>')
