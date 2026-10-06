from django.urls import path

from . import views

app_name = "findings"

urlpatterns = [
    path("<slug:code>/", views.finding_list, name="list"),
    path("<slug:code>/new/", views.finding_edit, name="create"),
    path("<slug:code>/<int:pk>/", views.finding_detail, name="detail"),
    path("<slug:code>/<int:pk>/edit/", views.finding_edit, name="edit"),
    path("<slug:code>/<int:pk>/review/", views.finding_review, name="review"),
]
