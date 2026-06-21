from functools import wraps

from flask import jsonify, request

from backend.services.auth_service import get_current_user


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        user = get_current_user(auth_header)

        if not user:
            return jsonify({
                "error": "unauthorized",
                "message": "A valid Bearer token is required."
            }), 401

        request.current_user = user
        return view_func(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            user = get_current_user(auth_header)

            if not user:
                return jsonify({
                    "error": "unauthorized",
                    "message": "A valid Bearer token is required."
                }), 401

            if user.role not in allowed_roles:
                return jsonify({
                    "error": "forbidden",
                    "message": "You do not have permission to access this resource."
                }), 403

            request.current_user = user
            return view_func(*args, **kwargs)

        return wrapper

    return decorator