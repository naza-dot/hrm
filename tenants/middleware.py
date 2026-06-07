from django.db import connection
from django.utils.deprecation import MiddlewareMixin


SAAS_PUBLIC_PATHS = [
    "/saas-admin/",
    "/admin/",
    "/login",
    "/register-company-admin/",
    "/health/",
    "/i18n/",
    "/accounts/",
    "/static/",
    "/media/",
]


class TenantSchemaMiddleware(MiddlewareMixin):
    """
    Sets the PostgreSQL search_path to the user's tenant schema.
    SAAS admin users and unauthenticated users on public paths stay on 'public'.
    """

    def process_request(self, request):
        for path in SAAS_PUBLIC_PATHS:
            if request.path_info.startswith(path):
                self._set_schema("public")
                return

        if getattr(request, "user", False) and request.user.is_authenticated:
            if not getattr(request.user, "is_saas_admin", False):
                self._set_schema_for_user(request)
                return

        self._set_schema("public")

    def _set_schema_for_user(self, request):
        from tenants.models import Client

        try:
            company = request.user.employee_get.employee_work_info.company_id
            tenant = Client.objects.filter(company=company, status="active").first()
            if tenant:
                self._set_schema(tenant.schema_name)
                return
        except Exception:
            pass

        for client in Client.objects.filter(status="active"):
            try:
                self._set_schema(client.schema_name)
                employee = request.user.employee_get
                if employee and client.company_id == employee.employee_work_info.company_id.id:
                    return
            except Exception:
                continue

        self._set_schema("public")

    def _set_schema(self, schema_name):
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}", public')
