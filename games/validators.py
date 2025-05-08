from functools import wraps
from uuid import UUID
from rest_framework.response import Response

def validate_uuid_param(param_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            value = kwargs.get(param_name)
            try:
                UUID(value)
            except (ValueError, TypeError):
                return Response({'detail': f'Invalid UUID for `{param_name}`'}, status=400)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
