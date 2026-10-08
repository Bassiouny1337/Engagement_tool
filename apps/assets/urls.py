from django.urls import path

from . import views

app_name = "assets"

urlpatterns = [
    path("<slug:code>/", views.asset_list, name="list"),
    path("<slug:code>/new/", views.asset_create, name="create"),
    path("<slug:code>/a/<slug:slug>/", views.asset_detail, name="detail"),
    path("<slug:code>/a/<slug:slug>/edit/", views.asset_edit, name="edit"),
    path("<slug:code>/a/<slug:slug>/delete/", views.asset_delete, name="delete"),
    path("<slug:code>/a/<slug:slug>/walkthrough/", views.walkthrough_edit, name="walkthrough"),
    path("<slug:code>/a/<slug:slug>/function/", views.add_function, name="add_function"),
    path("<slug:code>/a/<slug:slug>/service/", views.add_service, name="add_service"),
    path("<slug:code>/a/<slug:slug>/file/", views.add_file, name="add_file"),
    path("<slug:code>/a/<slug:slug>/credential/", views.add_credential, name="add_credential"),
    path("<slug:code>/a/<slug:slug>/cred/<int:pk>/reveal/", views.reveal_credential, name="reveal_credential"),
    path("<slug:code>/a/<slug:slug>/<str:model>/<int:pk>/delete/", views.delete_child, name="delete_child"),
]
