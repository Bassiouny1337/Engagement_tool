from django.urls import path

from . import views

app_name = "testcases"

urlpatterns = [
    path("<slug:code>/board/", views.board, name="board"),
    path("<slug:code>/tc/<int:pk>/status/", views.update_status, name="update_status"),
]
