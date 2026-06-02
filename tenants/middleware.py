import re
from django.http import HttpResponseForbidden

FEATURE_URL_MAP = [
    (r"^/recruitment", "recruitment"),
    (r"^/onboarding", "onboarding"),
    (r"^/employee", "employee"),
    (r"^/attendance", "attendance"),
    (r"^/leave", "leave"),
    (r"^/payroll", "payroll"),
    (r"^/pms", "pms"),
    (r"^/offboarding", "offboarding"),
    (r"^/asset", "asset"),
    (r"^/helpdesk", "helpdesk"),
    (r"^/project", "project"),
    (r"^/biometric", "biometric"),
    (r"^/notifications", "notifications"),
    (r"^/report", "report"),
]

PUBLIC_PATHS = [
    r"^/login",
    r"^/logout",
    r"^/admin/",
    r"^/static/",
    r"^/media/",
    r"^/health",
    r"^/i18n/",
    r"^/accounts/",
    r"^/change-password",
    r"^/two-factor",
    r"^/send-otp",
    r"^/api/",
]


class FeatureAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "urlconf", None) == "horilla.urls_public":
            return self.get_response(request)

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return self.get_response(request)

        path = request.path

        for pattern in PUBLIC_PATHS:
            if re.match(pattern, path):
                return self.get_response(request)

        for pattern, feature_slug in FEATURE_URL_MAP:
            if re.match(pattern, path):
                if not tenant.has_feature(feature_slug):
                    return HttpResponseForbidden(
                        f"Access denied. '{feature_slug}' is not included in your subscription."
                    )
                break

        return self.get_response(request)
