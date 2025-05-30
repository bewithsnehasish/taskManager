import json
import logging
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from projects.models import Project
from users.models import CustomUser
from users.utils import token_required

from .models import Category, Comment, Task, TaskAssignment, TaskAttachment

logger = logging.getLogger(__name__)


@csrf_exempt
@token_required
def create_task(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            project_id = data.get("project_id")
            title = data.get("title")
            description = data.get("description", "")
            priority = data.get("priority", "medium")
            status = data.get("status", "todo")
            category_id = data.get("category_id")
            due_date = data.get("due_date")
            is_milestone = data.get("is_milestone", False)
            depends_on_id = data.get("depends_on_id")
            tags = data.get("tags", "")
            estimated_hours = data.get("estimated_hours")
            assignee_ids = data.get("assignees", [])

            if not all([project_id, title]):
                return JsonResponse(
                    {"error": "Project ID and title are required"}, status=400
                )

            try:
                project = Project.objects.get(id=project_id)
                if (
                    request.user not in project.members.all()
                    and request.user != project.owner
                ):
                    return JsonResponse(
                        {"error": "Not authorized for this project"}, status=403
                    )
            except Project.DoesNotExist:
                return JsonResponse({"error": "Project not found"}, status=404)

            task = Task(
                project=project,
                title=title,
                description=description,
                created_by=request.user,
                priority=priority,
                status=status,
                is_milestone=is_milestone,
                tags=tags,
                estimated_hours=estimated_hours,
                due_date=datetime.fromisoformat(due_date) if due_date else None,
            )
            if category_id:
                try:
                    task.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    return JsonResponse({"error": "Category not found"}, status=404)
            if depends_on_id:
                try:
                    task.depends_on = Task.objects.get(
                        id=depends_on_id, project=project
                    )
                except Task.DoesNotExist:
                    return JsonResponse(
                        {"error": "Dependent task not found"}, status=404
                    )

            task.save()

            for assignee_id in assignee_ids:
                try:
                    user = CustomUser.objects.get(id=assignee_id)
                    TaskAssignment.objects.create(task=task, user=user)
                except CustomUser.DoesNotExist:
                    pass

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "status": task.status,
                        "category": task.category.name if task.category else None,
                        "due_date": (
                            task.due_date.isoformat() if task.due_date else None
                        ),
                        "is_milestone": task.is_milestone,
                        "depends_on": task.depends_on.id if task.depends_on else None,
                        "tags": task.tags,
                        "estimated_hours": (
                            float(task.estimated_hours)
                            if task.estimated_hours
                            else None
                        ),
                        "project": task.project.id,
                        "created_by": {
                            "id": task.created_by.id,
                            "email": task.created_by.email,
                        },
                        "assignees": [
                            {"id": a.user.id, "email": a.user.email, "status": a.status}
                            for a in task.assignments.all()
                        ],
                    },
                },
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Create task error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@token_required
def list_tasks(request):
    if request.method == "GET":
        try:
            tasks = (
                Task.objects.filter(project__owner=request.user)
                | Task.objects.filter(project__members=request.user)
                | Task.objects.filter(assignments__user=request.user)
            )
            tasks = tasks.distinct()

            status_filter = request.GET.get("status")
            priority_filter = request.GET.get("priority")
            category_id = request.GET.get("category_id")
            project_id = request.GET.get("project_id")
            sort = request.GET.get("sort", "-created_at")

            if status_filter:
                tasks = tasks.filter(status=status_filter)
            if priority_filter:
                tasks = tasks.filter(priority=priority_filter)
            if category_id:
                tasks = tasks.filter(category_id=category_id)
            if project_id:
                tasks = tasks.filter(project_id=project_id)
            tasks = tasks.order_by(sort)

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "tasks": [
                        {
                            "id": t.id,
                            "title": t.title,
                            "description": t.description,
                            "priority": t.priority,
                            "status": t.status,
                            "category": t.category.name if t.category else None,
                            "due_date": t.due_date.isoformat() if t.due_date else None,
                            "is_milestone": t.is_milestone,
                            "depends_on": t.depends_on.id if t.depends_on else None,
                            "tags": t.tags,
                            "estimated_hours": (
                                float(t.estimated_hours) if t.estimated_hours else None
                            ),
                            "actual_hours": (
                                float(t.actual_hours) if t.actual_hours else None
                            ),
                            "project": t.project.id,
                            "created_by": {
                                "id": t.created_by.id,
                                "email": t.created_by.email,
                            },
                            "assignees": [
                                {
                                    "id": a.user.id,
                                    "email": a.user.email,
                                    "status": a.status,
                                }
                                for a in t.assignments.all()
                            ],
                        }
                        for t in tasks
                    ],
                },
                status=200,
            )
        except Exception as e:
            logger.error(f"List tasks error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def update_task(request, task_id):
    if request.method == "PUT":
        try:
            task = Task.objects.get(id=task_id, project__owner=request.user)
            data = json.loads(request.body.decode("utf-8"))

            task.title = data.get("title", task.title)
            task.description = data.get("description", task.description)
            task.priority = data.get("priority", task.priority)
            task.status = data.get("status", task.status)
            task.is_milestone = data.get("is_milestone", task.is_milestone)
            task.tags = data.get("tags", task.tags)
            task.estimated_hours = data.get("estimated_hours", task.estimated_hours)
            task.actual_hours = data.get("actual_hours", task.actual_hours)
            task.due_date = (
                datetime.fromisoformat(data["due_date"])
                if data.get("due_date")
                else task.due_date
            )

            category_id = data.get("category_id")
            if category_id:
                try:
                    task.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    return JsonResponse({"error": "Category not found"}, status=404)

            depends_on_id = data.get("depends_on_id")
            if depends_on_id:
                try:
                    task.depends_on = Task.objects.get(
                        id=depends_on_id, project=task.project
                    )
                except Task.DoesNotExist:
                    return JsonResponse(
                        {"error": "Dependent task not found"}, status=404
                    )

            task.save()

            assignee_ids = data.get("assignees", [])
            task.assignments.all().delete()
            for assignee_id in assignee_ids:
                try:
                    user = CustomUser.objects.get(id=assignee_id)
                    TaskAssignment.objects.create(task=task, user=user)
                except CustomUser.DoesNotExist:
                    pass

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "priority": task.priority,
                        "status": task.status,
                        "category": task.category.name if task.category else None,
                        "due_date": (
                            task.due_date.isoformat() if task.due_date else None
                        ),
                        "is_milestone": task.is_milestone,
                        "depends_on": task.depends_on.id if task.depends_on else None,
                        "tags": task.tags,
                        "estimated_hours": (
                            float(task.estimated_hours)
                            if task.estimated_hours
                            else None
                        ),
                        "actual_hours": (
                            float(task.actual_hours) if task.actual_hours else None
                        ),
                        "project": task.project.id,
                        "created_by": {
                            "id": task.created_by.id,
                            "email": task.created_by.email,
                        },
                        "assignees": [
                            {"id": a.user.id, "email": a.user.email, "status": a.status}
                            for a in task.assignments.all()
                        ],
                    },
                },
                status=200,
            )
        except Task.DoesNotExist:
            return JsonResponse(
                {"error": "Task not found or not authorized"}, status=404
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Update task error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def delete_task(request, task_id):
    if request.method == "DELETE":
        try:
            task = Task.objects.get(id=task_id, project__owner=request.user)
            task.delete()
            return JsonResponse(
                {"message": "Request processed successfully, task deleted"},
                status=200,
            )
        except Task.DoesNotExist:
            return JsonResponse(
                {"error": "Task not found or not authorized"}, status=404
            )
        except Exception as e:
            logger.error(f"Delete task error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def create_comment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            task_id = data.get("task_id")
            content = data.get("content")

            if not all([task_id, content]):
                return JsonResponse(
                    {"error": "Task ID and content are required"}, status=400
                )

            try:
                task = Task.objects.get(id=task_id)
                if (
                    request.user not in task.project.members.all()
                    and request.user != task.project.owner
                ):
                    return JsonResponse(
                        {"error": "Not authorized for this task"}, status=403
                    )
            except Task.DoesNotExist:
                return JsonResponse({"error": "Task not found"}, status=404)

            comment = Comment(task=task, author=request.user, content=content)
            comment.save()

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "comment": {
                        "id": comment.id,
                        "task_id": comment.task.id,
                        "author": {
                            "id": comment.author.id,
                            "email": comment.author.email,
                        },
                        "content": comment.content,
                        "created_at": comment.created_at.isoformat(),
                    },
                },
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Create comment error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@token_required
def list_comments(request, task_id):
    if request.method == "GET":
        try:
            task = Task.objects.get(id=task_id)
            if (
                request.user not in task.project.members.all()
                and request.user != task.project.owner
            ):
                return JsonResponse(
                    {"error": "Not authorized for this task"}, status=403
                )

            comments = task.comments.all()
            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "comments": [
                        {
                            "id": c.id,
                            "task_id": c.task.id,
                            "author": {"id": c.author.id, "email": c.author.email},
                            "content": c.content,
                            "created_at": c.created_at.isoformat(),
                        }
                        for c in comments
                    ],
                },
                status=200,
            )
        except Task.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)
        except Exception as e:
            logger.error(f"List comments error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def upload_attachment(request, task_id):
    if request.method == "POST":
        try:
            task = Task.objects.get(id=task_id)
            if (
                request.user not in task.project.members.all()
                and request.user != task.project.owner
            ):
                return JsonResponse(
                    {"error": "Not authorized for this task"}, status=403
                )

            file = request.FILES.get("file")
            if not file:
                return JsonResponse({"error": "File is required"}, status=400)

            attachment = TaskAttachment(
                task=task,
                file=file,
                filename=file.name,
                file_type=file.content_type,
                uploaded_by=request.user,
            )
            attachment.save()

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "attachment": {
                        "id": attachment.id,
                        "task_id": attachment.task.id,
                        "filename": attachment.filename,
                        "file_type": attachment.file_type,
                        "file_url": attachment.file.url,
                        "uploaded_by": {
                            "id": attachment.uploaded_by.id,
                            "email": attachment.uploaded_by.email,
                        },
                        "uploaded_at": attachment.uploaded_at.isoformat(),
                    },
                },
                status=201,
            )
        except Task.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)
        except Exception as e:
            logger.error(f"Upload attachment error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@token_required
def list_attachments(request, task_id):
    if request.method == "GET":
        try:
            task = Task.objects.get(id=task_id)
            if (
                request.user not in task.project.members.all()
                and request.user != task.project.owner
            ):
                return JsonResponse(
                    {"error": "Not authorized for this task"}, status=403
                )

            attachments = task.attachments.all()
            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "attachments": [
                        {
                            "id": a.id,
                            "task_id": a.task.id,
                            "filename": a.filename,
                            "file_type": a.file_type,
                            "file_url": a.file.url,
                            "uploaded_by": {
                                "id": a.uploaded_by.id,
                                "email": a.uploaded_by.email,
                            },
                            "uploaded_at": a.uploaded_at.isoformat(),
                        }
                        for a in attachments
                    ],
                },
                status=200,
            )
        except Task.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)
        except Exception as e:
            logger.error(f"List attachments error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def create_category(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get("name")
            description = data.get("description", "")

            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)

            category = Category(name=name, description=description)
            category.save()

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "category": {
                        "id": category.id,
                        "name": category.name,
                        "description": category.description,
                    },
                },
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Create category error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@token_required
def list_categories(request):
    if request.method == "GET":
        try:
            categories = Category.objects.all()
            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "categories": [
                        {"id": c.id, "name": c.name, "description": c.description}
                        for c in categories
                    ],
                },
                status=200,
            )
        except Exception as e:
            logger.error(f"List categories error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)
