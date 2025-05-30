import uuid

from django.http import JsonResponse
from users.models import CustomUser


def token_required(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Invalid authToken"}, status=401)

        token = auth_header.split(" ")[1]
        try:
            uuid_token = uuid.UUID(token)
            user = CustomUser.objects.filter(authToken=uuid_token).first()
            if not user:
                return JsonResponse({"error": "Invalid authToken"}, status=401)
            request.user = user  # Attach user to request
            return view_func(request, *args, **kwargs)
        except ValueError:
            return JsonResponse({"error": "Invalid authToken"}, status=401)
        except Exception as e:
            return JsonResponse({"error": "Invalid authToken"}, status=401)

    return wrapper
