import json
import logging
import uuid

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser
from .utils import token_required

logger = logging.getLogger(__name__)


@csrf_exempt
def register(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            email = data.get("email")
            username = data.get("username")
            first_name = data.get("first_name")
            last_name = data.get("last_name")
            password = data.get("password")

            if not all([email, username, first_name, last_name, password]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists"}, status=409)

            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists"}, status=409)

            user = CustomUser(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )
            user.save()

            return JsonResponse(
                {
                    "message": "Registration successful",
                    "user": {
                        "authToken": str(user.authToken),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                },
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def login_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            email = data.get("email")
            password = data.get("password")

            if not all([email, password]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            try:
                user = CustomUser.objects.filter(email=email, password=password).first()
                if not user:
                    return JsonResponse({"error": "Invalid credentials"}, status=401)
            except CustomUser.DoesNotExist:
                return JsonResponse({"error": "Invalid credentials"}, status=401)

            user.authToken = uuid.uuid4()
            user.save()
            if user is not None:
                return JsonResponse(
                    {
                        "message": "Login successful",
                        "user": {
                            "authToken": str(user.authToken),
                            "email": user.email,
                            "username": user.username,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        },
                    },
                    status=200,
                )
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def profile(request):
    if request.method == "GET":
        user = request.user
        return JsonResponse(
            {
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "authToken": str(user.authToken),
            },
            status=200,
        )

    elif request.method == "PUT":
        try:
            data = json.loads(request.body.decode("utf-8"))
            user = request.user
            user.username = data.get("username", user.username)
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            user.password = data.get("password", user.password)

            user.save()
            return JsonResponse(
                {
                    "message": "Request processed successfully",
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "authToken": str(user.authToken),
                },
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@token_required
def list_users(request):
    if request.method == "GET":
        try:
            users = CustomUser.objects.all()
            user_list = [
                {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                }
                for user in users
            ]
            return JsonResponse(
                {
                    "message": "Users retrieved successfully",
                    "users": user_list,
                },
                status=200,
            )
        except Exception as e:
            logger.error(f"List users error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)
