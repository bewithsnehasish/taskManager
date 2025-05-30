from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("projects/", views.list_projects, name="list_projects"),
    path("projects/create/", views.create_project, name="create_project"),
    path("projects/<int:project_id>/", views.update_project, name="update_project"),
    path(
        "projects/<int:project_id>/delete/", views.delete_project, name="delete_project"
    ),
]
