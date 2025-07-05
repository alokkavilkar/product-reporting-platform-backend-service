from django.http import JsonResponse
import os

def requires_role(required_role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            roles = request.auth.get(os.environ.get('ROLE_NAMESPACE'), [])
            if required_role not in roles:
                return JsonResponse({"message": "Forbidden: insufficient role"}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator