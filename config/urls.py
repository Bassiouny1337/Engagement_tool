from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("engagements/", include("apps.engagements.urls")),
    path("testcases/", include("apps.testcases.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("findings/", include("apps.findings.urls")),
    path("reports/", include("apps.reporting.urls")),
    path("scans/", include("apps.scans.urls")),
    path("notebook/", include("apps.notebook.urls")),
    path("assets/", include("apps.assets.urls")),
    path("", include("apps.dashboard.urls")),
]
