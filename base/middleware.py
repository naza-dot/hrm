"""
middleware.py
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from base.backends import ConfiguredEmailBackend
from horilla.horilla_apps import TWO_FACTORS_AUTHENTICATION


class ForcePasswordChangeMiddleware:
    """
    Middleware to force password change for new employees.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        excluded_paths = ["/change-password", "/login", "/logout"]
        if request.path.rstrip("/") in excluded_paths:
            return self.get_response(request)

        if hasattr(request, "user") and request.user.is_authenticated:
            if getattr(request.user, "is_new_employee", True):
                return redirect("change-password")

        return self.get_response(request)


class TwoFactorAuthMiddleware:
    """
    Middleware to enforce two-factor authentication for specific users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        excluded_paths = [
            "/change-password",
            "/login",
            "/logout",
            "/two-factor",
            "/send-otp",
        ]

        if request.path.rstrip("/") in excluded_paths:
            return self.get_response(request)

        if TWO_FACTORS_AUTHENTICATION:
            try:
                if ConfiguredEmailBackend().configuration is not None:
                    if hasattr(request, "user") and request.user.is_authenticated:
                        if not request.session.get("otp_code_verified", False):
                            return redirect("/two-factor")
                else:
                    return self.get_response(request)
            except Exception as e:
                return self.get_response(request)

        return self.get_response(request)
