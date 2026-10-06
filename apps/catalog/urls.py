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
]
