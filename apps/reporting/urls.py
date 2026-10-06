from django.urls import path

from . import views

app_name = "reporting"

urlpatterns = [
    path("<slug:code>/preview/", views.report_preview, name="preview"),
    path("<slug:code>/download/", views.report_download, name="download"),
]
