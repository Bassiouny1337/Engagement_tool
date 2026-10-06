from django.urls import path

from . import views

app_name = "scans"

urlpatterns = [
    path("<slug:code>/", views.scan_list, name="list"),
    path("<slug:code>/upload/", views.scan_upload, name="upload"),
    path("<slug:code>/<int:pk>/", views.scan_detail, name="detail"),
    path("<slug:code>/<int:pk>/scope/", views.add_scope_from_host, name="add_scope"),
    path("<slug:code>/<int:pk>/testcase/", views.add_testcase_from_service, name="add_testcase"),
]
