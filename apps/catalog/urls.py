from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.catalog_home, name="home"),
    path("checklists/", views.checklist_list, name="checklist_list"),
    path("checklists/new/", views.checklist_edit, name="checklist_new"),
    path("checklists/<int:pk>/edit/", views.checklist_edit, name="checklist_edit"),
    path("checklists/<int:pk>/delete/", views.checklist_delete, name="checklist_delete"),
    path("scenarios/", views.scenario_list, name="scenario_list"),
    path("scenarios/new/", views.scenario_edit, name="scenario_new"),
    path("scenarios/<int:pk>/edit/", views.scenario_edit, name="scenario_edit"),
    path("scenarios/<int:pk>/delete/", views.scenario_delete, name="scenario_delete"),
    # Personal catalog
    path("mine/", views.my_catalog, name="mine"),
    path("mine/checklist/new/", views.my_checklist_edit, name="my_checklist_new"),
    path("mine/checklist/<int:pk>/edit/", views.my_checklist_edit, name="my_checklist_edit"),
    path("mine/scenario/new/", views.my_scenario_edit, name="my_scenario_new"),
    path("mine/scenario/<int:pk>/edit/", views.my_scenario_edit, name="my_scenario_edit"),
    path("mine/<str:kind>/<int:pk>/delete/", views.my_item_delete, name="my_item_delete"),
    path("mine/<str:kind>/<int:pk>/request/", views.request_promotion, name="request_promotion"),
    # Contribution review
    path("contributions/", views.contribution_list, name="contributions"),
    path("contributions/<int:pk>/approve/", views.contribution_approve, name="contribution_approve"),
    path("contributions/<int:pk>/reject/", views.contribution_reject, name="contribution_reject"),
]
