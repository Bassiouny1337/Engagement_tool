from django.urls import path

from . import views

app_name = "engagements"

urlpatterns = [
    path("", views.engagement_list, name="list"),
    path("new/", views.engagement_create, name="create"),
    path("<slug:code>/", views.engagement_detail, name="detail"),
    path("<slug:code>/domains/add/", views.add_domain, name="add_domain"),
    path("<slug:code>/status/", views.change_status, name="change_status"),
    path("<slug:code>/scope/add/", views.add_scope_item, name="add_scope"),
    path("<slug:code>/scope/<int:pk>/remove/", views.remove_scope_item, name="remove_scope"),
]
