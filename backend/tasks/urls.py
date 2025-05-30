from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("tasks/", views.list_tasks, name="list_tasks"),
    path("tasks/create/", views.create_task, name="create_task"),
    path("tasks/<int:task_id>/", views.update_task, name="update_task"),
    path("tasks/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path("comments/create/", views.create_comment, name="create_comment"),
    path("tasks/<int:task_id>/comments/", views.list_comments, name="list_comments"),
    path(
        "tasks/<int:task_id>/attachments/create/",
        views.upload_attachment,
        name="upload_attachment",
    ),
    path(
        "tasks/<int:task_id>/attachments/",
        views.list_attachments,
        name="list_attachments",
    ),
    path("categories/create/", views.create_category, name="create_category"),
    path("categories/", views.list_categories, name="list_categories"),
]
