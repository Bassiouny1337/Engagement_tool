from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    """Landing dashboard. Populated with real metrics in later milestones."""
    context = {
        "user_role": request.user.get_role_display(),
        "capabilities": sorted(
            c for c in [
                "manage_users", "manage_engagements", "edit_testcases",
                "manage_findings", "review", "sign_off", "import_scans",
                "export_reports", "view_audit_log",
            ] if request.user.has_capability(c)
        ),
    }
    return render(request, "dashboard/home.html", context)
