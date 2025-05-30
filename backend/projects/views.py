import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from users.models import CustomUser
from users.utils import token_required

from .models import Project

logger = logging.getLogger(__name__)


@csrf_exempt
@token_required
def create_project(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get("name")
            description = data.get("description", "")
            deadline = data.get("deadline")
            status = data.get("status", "active")
            member_ids = data.get("members", [])

            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)

            project = Project(
                name=name,
                description=description,
                owner=request.user,
                deadline=deadline,
                status=status,
            )
            project.save()

            for member_id in member_ids:
                try:
                    member = CustomUser.objects.get(id=member_id)
                    project.members.add(member)
                except CustomUser.DoesNotExist:
                    pass

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "status": project.status,
                        "deadline": (
                            project.deadline.isoformat() if project.deadline else None
                        ),
                        "owner": {"id": project.owner.id, "email": project.owner.email},
                        "members": [
                            {"id": m.id, "email": m.email}
                            for m in project.members.all()
                        ],
                    },
                },
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Create project error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@token_required
def list_projects(request):
    if request.method == "GET":
        try:
            projects = Project.objects.filter(
                owner=request.user
            ) | Project.objects.filter(members=request.user)
            projects = projects.distinct()
            status_filter = request.GET.get("status")
            if status_filter:
                projects = projects.filter(status=status_filter)

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "projects": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "description": p.description,
                            "status": p.status,
                            "deadline": p.deadline.isoformat() if p.deadline else None,
                            "owner": {"id": p.owner.id, "email": p.owner.email},
                            "members": [
                                {"id": m.id, "email": m.email} for m in p.members.all()
                            ],
                        }
                        for p in projects
                    ],
                },
                status=200,
            )
        except Exception as e:
            logger.error(f"List projects error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def update_project(request, project_id):
    if request.method == "PUT":
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
            data = json.loads(request.body.decode("utf-8"))
            project.name = data.get("name", project.name)
            project.description = data.get("description", project.description)
            project.status = data.get("status", project.status)
            project.deadline = data.get("deadline", project.deadline)
            project.save()

            member_ids = data.get("members", [])
            project.members.clear()
            for member_id in member_ids:
                try:
                    member = CustomUser.objects.get(id=member_id)
                    project.members.add(member)
                except CustomUser.DoesNotExist:
                    pass

            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "status": project.status,
                        "deadline": (
                            project.deadline.isoformat() if project.deadline else None
                        ),
                        "owner": {"id": project.owner.id, "email": project.owner.email},
                        "members": [
                            {"id": m.id, "email": m.email}
                            for m in projects.members.all()
                        ],
                    },
                },
                status=200,
            )
        except Project.DoesNotExist:
            return JsonResponse(
                {"error": "Project not found or not authorized"}, status=404
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Update project error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def delete_project(request, project_id):
    if request.method == "DELETE":
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
            project.delete()
            return JsonResponse(
                {"message": "Request processed successfully, project deleted"},
                status=200,
            )
        except Project.DoesNotExist:
            return JsonResponse(
                {"error": "Project not found or not authorized"}, status=404
            )
        except Exception as e:
            logger.error(f"Delete project error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)
