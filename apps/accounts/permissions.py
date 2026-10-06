"""Reusable capability checks for views.

Usage:
    @require_capability("manage_engagements")
    def my_view(request): ...
"""
from functools import wraps

from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def require_capability(capability):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or not user.has_capability(capability):
                raise PermissionDenied(
                    f"Your role lacks the '{capability}' capability."
                )
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


class HasCapability(BasePermission):
    """DRF permission: set `required_capability` on the view."""

    def has_permission(self, request, view):
        capability = getattr(view, "required_capability", None)
        if capability is None:
            return request.user.is_authenticated
        return (
            request.user.is_authenticated
            and request.user.has_capability(capability)
        )
