from django.urls import path

from . import views

app_name = "notebook"

urlpatterns = [
    path("<slug:code>/", views.notebook_home, name="home"),
    path("<slug:code>/new/", views.page_edit, name="create"),
    path("<slug:code>/preview/", views.preview, name="preview"),
    path("<slug:code>/p/<slug:slug>/", views.page_view, name="page"),
    path("<slug:code>/p/<slug:slug>/edit/", views.page_edit, name="edit"),
    path("<slug:code>/p/<slug:slug>/delete/", views.page_delete, name="delete"),
]
