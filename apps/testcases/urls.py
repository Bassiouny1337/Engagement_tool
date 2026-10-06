from django.urls import path

from . import views

app_name = "testcases"

urlpatterns = [
    path("<slug:code>/board/", views.board, name="board"),
    path("<slug:code>/tc/<int:pk>/status/", views.update_status, name="update_status"),
    path("<slug:code>/tc/<int:pk>/notes/", views.update_notes, name="update_notes"),
    path("<slug:code>/add/", views.add_custom, name="add_custom"),
    path("<slug:code>/library/", views.scenario_library, name="scenario_library"),
    path("<slug:code>/library/<int:scenario_id>/pull/", views.pull_scenario, name="pull_scenario"),
]
