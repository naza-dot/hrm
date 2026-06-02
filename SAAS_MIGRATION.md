# SaaS Multi-Tenant Migration Guide: Schema-per-Tenant with django-tenants

## Architecture Overview

```
                        ┌──────────────────────────────────┐
                        │         Public Schema             │
                        │  (shared data: tenants, domains,  │
                        │   users, auth, sessions)          │
                        └──────┬───────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
       ┌────────▼────┐ ┌──────▼──────┐ ┌─────▼─────────┐
       │ Tenant A    │ │ Tenant B    │ │ Tenant C      │
       │ Schema      │ │ Schema      │ │ Schema        │
       │ (all HRM    │ │ (all HRM    │ │ (all HRM      │
       │  tables)    │ │  tables)    │ │  tables)      │
       └─────────────┘ └─────────────┘ └───────────────┘
```

- **Public schema**: tenants registry, domains, user accounts, sessions
- **Each tenant schema**: full copy of all HRM tables (employee, recruitment, payroll, etc.)

---

## Step 1: Install django-tenants

```bash
pip install django-tenants
```

Add to `requirements.txt`:

```
django-tenants
```

---

## Step 2: Create the Tenants App

```bash
python manage.py startapp tenants
```

### 2a. Tenant Model (`tenants/models.py`)

```python
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    """
    Each Client = one customer company = one schema.
    """
    name = models.CharField(max_length=100, verbose_name="Company Name")
    schema_name = models.CharField(max_length=63, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    paid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Feature subscription flags — this is the "feature selection" you asked for
    FEATURES = {
        "recruitment": "Recruitment & Hiring",
        "onboarding": "Employee Onboarding",
        "employee": "Employee Management",
        "attendance": "Attendance Tracking",
        "leave": "Leave Management",
        "payroll": "Payroll Processing",
        "pms": "Performance Management",
        "offboarding": "Offboarding",
        "asset": "Asset Management",
        "helpdesk": "Helpdesk / Ticketing",
        "project": "Project Management",
        "biometric": "Biometric Integration",
        "notifications": "Notifications & Alerts",
        "report": "Reports & Analytics",
    }

    features = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Subscribed Features",
        help_text="JSON object of feature booleans, e.g. {'recruitment': true, 'payroll': false}",
    )

    # Max employees allowed (null = unlimited)
    max_employees = models.IntegerField(null=True, blank=True)

    # Auto-create schema on save
    auto_create_schema = True
    auto_drop_schema = True

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    def has_feature(self, feature_slug):
        """Check if tenant has access to a feature."""
        return self.features.get(feature_slug, False)


class Domain(DomainMixin):
    """
    Each tenant has one or more domains/subdomains.
    e.g. acme.hrm.yourplatform.com, acme-custom.com
    """
    pass
```

### 2b. Tenant App Config (`tenants/apps.py`)

```python
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tenants"
```

### 2c. Tenant Admin (`tenants/admin.py`) — Your SaaS Portal

```python
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain


class DomainInline(admin.TabularInline):
    model = Domain
    max_num = 1


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ["name", "schema_name", "is_active", "paid_until", "created_at"]
    list_filter = ["is_active", "features"]
    search_fields = ["name", "schema_name", "email"]
    inlines = [DomainInline]

    fieldsets = [
        ("Company Info", {
            "fields": ["name", "schema_name", "email", "phone", "address"]
        }),
        ("Subscription", {
            "fields": ["is_active", "paid_until", "max_employees", "features"],
            "description": "Toggle which features this customer has access to.",
        }),
    ]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]
    list_filter = ["is_primary"]
```

---

## Step 3: Update Django Settings

### 3a. Modify `horilla/settings.py`

```python
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, "django-insecure-..."),
    ALLOWED_HOSTS=(list, ["*"]),
    CSRF_TRUSTED_ORIGINS=(list, ["http://localhost:8000"]),
)

env.read_env(os.path.join(BASE_DIR, ".env"), overwrite=True)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ── django-tenants: must be first ──────────────────────────
SHARED_APPS = [
    "django_tenants",  # mandatory
    "tenants",          # your tenant model lives here

    # These run in the PUBLIC schema only
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "corsheaders",
    "widget_tweaks",
    "django_filters",
    "simple_history",
    "mathfilters",
    "django_apscheduler",
]

TENANT_APPS = [
    # These get cloned into EACH tenant schema
    "base",
    "employee",
    "recruitment",
    "leave",
    "pms",
    "onboarding",
    "asset",
    "attendance",
    "payroll",
    "notifications",
    "horilla_audit",
    "horilla_widgets",
    "horilla_crumbs",
    "horilla_documents",
    "horilla_views",
    "horilla_automations",
    "auditlog",
    "biometric",
    "helpdesk",
    "offboarding",
    "project",
    "accessibility",
    "horilla_backup",
    "dynamic_fields",
    "facedetection",
    "geofencing",
    "report",
    "outlook_auth",
]

INSTALLED_APPS = SHARED_APPS + TENANT_APPS

# ── django-tenants core setting ─────────────────────────────
TENANT_MODEL = "tenants.Client"
TENANT_DOMAIN_MODEL = "tenants.Domain"

# ── Database ─────────────────────────────────────────────────
# Single database server, multiple schemas
if env("DATABASE_URL", default=None):
    DATABASES = {
        "default": env.db(),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django_tenants.postgresql_backend",
            "NAME": env("DB_NAME", default="horilla_saas"),
            "USER": env("DB_USER", default="postgres"),
            "PASSWORD": env("DB_PASSWORD", default="postgres"),
            "HOST": env("DB_HOST", default="db"),
            "PORT": env("DB_PORT", default="5432"),
        }
    }

# ── Database router ─────────────────────────────────────────
DATABASE_ROUTERS = ["django_tenants.routers.TenantSyncRouter"]

# ── Middleware ───────────────────────────────────────────────
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",  # must be early
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "horilla_api.middleware.RejectBasicAuthMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Your feature-access middleware (see Step 6)
    "tenants.middleware.FeatureAccessMiddleware",
]

ROOT_URLCONF = "horilla.urls"
WSGI_APPLICATION = "horilla.wsgi.application"

# ── Static & Media ───────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Auth ─────────────────────────────────────────────────────
LOGIN_URL = "/login"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# ── Internationalization ─────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="Asia/Kolkata")
USE_I18N = True
USE_L10N = True
USE_TZ = True
SITE_ID = 1
```

### 3b. Remove old middleware registrations in `horilla/horilla_middlewares.py`

The `CompanyMiddleware` is no longer needed since schema isolation handles it.

```python
import threading
from django.http import HttpResponseNotAllowed
from django.shortcuts import render
from horilla.settings import MIDDLEWARE

# REMOVED: CompanyMiddleware — schema isolation replaces it

MIDDLEWARE.append("horilla.horilla_middlewares.MethodNotAllowedMiddleware")
MIDDLEWARE.append("horilla.horilla_middlewares.ThreadLocalMiddleware")
MIDDLEWARE.append("horilla.horilla_middlewares.SVGSecurityMiddleware")

MIDDLEWARE.append("base.middleware.ForcePasswordChangeMiddleware")
MIDDLEWARE.append("base.middleware.TwoFactorAuthMiddleware")

_thread_locals = threading.local()


class ThreadLocalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response


class MethodNotAllowedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, HttpResponseNotAllowed):
            return render(request, "405.html")
        return response


class SVGSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.endswith(".svg") and response.status_code == 200:
            response["Content-Security-Policy"] = (
                "default-src 'none'; style-src 'unsafe-inline';"
            )
            response["X-Content-Type-Options"] = "nosniff"
        return response
```

Also update `horilla/horilla_apps.py` — remove the `CompanyMiddleware`-related logic:

```python
from horilla import settings
from horilla.settings import INSTALLED_APPS

INSTALLED_APPS.append("accessibility")
INSTALLED_APPS.append("horilla_audit")
INSTALLED_APPS.append("horilla_widgets")
INSTALLED_APPS.append("horilla_crumbs")
INSTALLED_APPS.append("horilla_documents")
INSTALLED_APPS.append("horilla_views")
INSTALLED_APPS.append("horilla_automations")
INSTALLED_APPS.append("auditlog")
INSTALLED_APPS.append("biometric")
INSTALLED_APPS.append("helpdesk")
INSTALLED_APPS.append("offboarding")
INSTALLED_APPS.append("horilla_backup")
INSTALLED_APPS.append("project")

# REMOVED: storages conditional — handle separately if needed

AUDITLOG_INCLUDE_ALL_MODELS = True
AUDITLOG_EXCLUDE_TRACKING_MODELS = ()

setattr(settings, "AUDITLOG_INCLUDE_ALL_MODELS", AUDITLOG_INCLUDE_ALL_MODELS)
setattr(settings, "AUDITLOG_EXCLUDE_TRACKING_MODELS", AUDITLOG_EXCLUDE_TRACKING_MODELS)

settings.MIDDLEWARE.append("auditlog.middleware.AuditlogMiddleware")

SETTINGS_EMAIL_BACKEND = getattr(settings, "EMAIL_BACKEND", False)
setattr(settings, "EMAIL_BACKEND", "base.backends.ConfiguredEmailBackend")
if SETTINGS_EMAIL_BACKEND:
    setattr(settings, "EMAIL_BACKEND", SETTINGS_EMAIL_BACKEND)

# These can remain but become per-tenant settings:
SIDEBARS = [
    "recruitment", "onboarding", "employee", "attendance",
    "leave", "payroll", "pms", "offboarding", "asset",
    "helpdesk", "project",
]

WHITE_LABELLING = False
NESTED_SUBORDINATE_VISIBILITY = False
TWO_FACTORS_AUTHENTICATION = False
```

---

## Step 4: Remove the Old Company Model & HorillaCompanyManager

Since schema-per-tenant means each tenant's schema is fully isolated, the `Company` model and `HorillaCompanyManager` are no longer needed.

### 4a. Remove/replace `Company` references

The `Company` model in `base/models.py` and all `company_id` fields, `HorillaCompanyManager` usage, and `company_filter` logic should be removed. Every model that previously had a `company_id` FK or `HorillaCompanyManager` now simply lives in the tenant's schema — no company filter needed.

**Pattern for each model change:**

```python
# BEFORE
class Department(models.Model):
    company_id = models.ManyToManyField(Company, blank=True)
    objects = HorillaCompanyManager("company_id")

# AFTER
class Department(models.Model):
    # No company_id — schema isolation handles multi-tenancy
    objects = models.Manager()  # standard Django manager
```

### 4b. Files to modify

| File | Change |
|------|--------|
| `base/models.py` | Remove `Company` model, all `company_id` fields, all `HorillaCompanyManager` usage, remove `company_filter` logic |
| `base/horilla_company_manager.py` | Delete this file entirely |
| `base/middleware.py` | Delete or gut `CompanyMiddleware` class (keep `ForcePasswordChangeMiddleware` and `TwoFactorAuthMiddleware`) |
| `base/decorators.py` | Remove any `company_filter` decorators |
| `base/context_processors.py` | Remove company context processors |
| `employee/models.py` | Remove `company_id` fields |
| `recruitment/models.py` | Remove `company_id` fields |
| `leave/models.py` | Remove `company_id` fields |
| `attendance/models.py` | Remove `company_id` fields |
| `payroll/models.py` | Remove `company_id` fields |
| `asset/models.py` | Remove `company_id` fields |
| `helpdesk/models.py` | Remove `company_id` fields |
| `offboarding/models.py` | Remove `company_id` fields |
| `pms/models.py` | Remove `company_id` fields |
| `project/models.py` | Remove `company_id` fields |
| `horilla_api/api_serializers/base/serializers.py` | Remove `company_id` serialization |
| `horilla_api/api_serializers/leave/serializers.py` | Remove `company_id` exclusion |
| `horilla_api/api_serializers/asset/serializers.py` | Remove `company_id` exclusion |
| `horilla_api/api_serializers/payroll/serializers.py` | Remove `company_id` read-only field |
| `horilla_api/api_views/auth/views.py` | Remove `company_id` from login response |

### 4c. Remove `company_filter` from all model `Meta` / `filter` references

Search for `company_filter` across the codebase and remove it.

```bash
grep -rn "company_filter" /workspace/hrm/ --include="*.py"
```

---

## Step 5: Update WSGI to Use django-tenants

### `horilla/wsgi.py`

```python
import os
from django.core.wsgi import get_wsgi_application
from django_tenants.utils import set_tenant

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")

application = get_wsgi_application()
```

---

## Step 6: Feature Access Middleware

Create `tenants/middleware.py` — this enforces that a customer can only access the features they've subscribed to.

```python
import re
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django_tenants.utils import get_tenant_model


# Map URL prefixes to feature slugs
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

# Paths that should never be blocked
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
    """
    Blocks access to features the tenant hasn't subscribed to.
    Only runs for tenant schemas (not public schema).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for public schema (admin portal, login, etc.)
        if getattr(request, "urlconf", None) == "horilla.urls_public":
            return self.get_response(request)

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return self.get_response(request)

        path = request.path

        # Skip public paths
        for pattern in PUBLIC_PATHS:
            if re.match(pattern, path):
                return self.get_response(request)

        # Check feature access
        for pattern, feature_slug in FEATURE_URL_MAP:
            if re.match(pattern, path):
                if not tenant.has_feature(feature_slug):
                    return HttpResponseForbidden(
                        f"Access denied. '{feature_slug}' is not included in your subscription."
                    )
                break

        return self.get_response(request)
```

---

## Step 7: URL Routing — Separate Public from Tenant

### `horilla/urls_public.py` (public schema routes)

```python
"""URLs served from the PUBLIC schema (login, tenant selection, admin)"""

from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check),
    path("accounts/", include("django.contrib.auth.urls")),
]
```

### `horilla/urls.py` (tenant schema routes)

```python
"""URLs served from TENANT schemas (all HRM functionality)"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
import notifications.urls

from . import settings


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("base.urls")),
    path("", include("horilla_automations.urls")),
    path("", include("horilla_views.urls")),
    path("employee/", include("employee.urls")),
    path("horilla-widget/", include("horilla_widgets.urls")),
    path("api/", include("horilla_api.urls")),
    re_path(
        "^inbox/notifications/",
        include(notifications.urls, namespace="notifications"),
    ),
    path("i18n/", include("django.conf.urls.i18n")),
    path("health/", health_check),
]
```

### `horilla/settings.py` — tell django-tenants about the split

Add after `TENANT_MODEL`:

```python
PUBLIC_SCHEMA_URLCONF = "horilla.urls_public"
```

Students should also set `TENANT_ROUTING_PREFIX` or handle via domain routing — django-tenants automatically uses the domain to determine the tenant and routes to `PUBLIC_SCHEMA_URLCONF` for the public schema domain.

---

## Step 8: Data Migration Strategy

### 8a. Create initial migrations for the tenants app

```bash
python manage.py makemigrations tenants
python manage.py migrate_schemas --shared
```

### 8b. Create the public tenant (your platform)

```python
from tenants.models import Client, Domain

# Create the public tenant
public_tenant = Client(
    schema_name="public",
    name="Platform Admin",
    is_active=True,
    features={feature: True for feature in Client.FEATURES},
)
public_tenant.save()

# Add domain for public tenant
Domain.objects.create(
    domain="hrm.yourplatform.com",
    tenant=public_tenant,
    is_primary=True,
)
```

### 8c. Migrate existing data into a tenant schema

If you already have data in a non-tenant database, write a migration script:

```python
"""
Script: migrate_existing_data.py

Run this once to move existing data from the old single-DB setup
into the first tenant schema.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")
django.setup()

from django.db import connection
from django_tenants.utils import get_tenant_model, schema_context
from django.contrib.auth import get_user_model

User = get_user_model()

# Create first customer tenant
tenant = get_tenant_model()(
    schema_name="customer1",
    name="Customer Company Name",
    is_active=True,
    paid_until="2027-01-01",
    features={
        "recruitment": True,
        "employee": True,
        "payroll": True,
        "leave": True,
        "attendance": True,
        "onboarding": True,
        "pms": False,
        "offboarding": False,
        "asset": True,
        "helpdesk": False,
        "project": False,
    },
)
tenant.save()

# Add domain
from tenants.models import Domain
Domain.objects.create(
    domain="customer1.hrm.yourplatform.com",
    tenant=tenant,
    is_primary=True,
)

print(f"Tenant '{tenant.name}' created with schema '{tenant.schema_name}'.")
print("Now run: python manage.py migrate_schemas")
print("Then deploy with your domain routing and the schema will be created automatically.")
```

### 8d. Run migrations for all schemas

```bash
# Create tables in public schema
python manage.py migrate_schemas --shared

# Create tables in each tenant schema (including new ones)
python manage.py migrate_schemas
```

---

## Step 9: Onboarding Flow (New Customer)

When a new customer signs up:

```python
"""
tenants/onboarding.py — call this when a new customer subscribes
"""

from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from .models import Client, Domain


def provision_new_tenant(
    company_name,
    domain,
    schema_name,
    features,
    admin_email,
    admin_password,
    paid_until=None,
    max_employees=None,
):
    """
    Provision a new tenant:
    1. Create Client record (auto-creates schema)
    2. Create Domain
    3. Run migrations on the new schema
    4. Create admin user inside the tenant schema
    """
    # 1. Create tenant
    tenant = Client.objects.create(
        schema_name=schema_name,
        name=company_name,
        features=features,
        paid_until=paid_until,
        max_employees=max_employees,
        is_active=True,
    )

    # 2. Add domain
    Domain.objects.create(
        domain=domain,
        tenant=tenant,
        is_primary=True,
    )

    # 3. Run migrations on the new schema
    from django.core.management import call_command
    from io import StringIO
    out = StringIO()
    call_command("migrate_schemas", schema_name=schema_name, stdout=out)
    print(out.getvalue())

    # 4. Create admin user inside the tenant schema
    with schema_context(schema_name):
        User = get_user_model()
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                username="admin",
                email=admin_email,
                password=admin_password,
            )

    return tenant
```

---

## Step 10: Update Docker Compose

### `docker-compose.yaml`

```yaml
services:
  server:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8010:8000"
    restart: unless-stopped
    environment:
      DATABASE_URL: "postgres://postgres:postgres@db:5432/horilla_saas"
      DJANGO_SETTINGS_MODULE: "horilla.settings"
    command: sh ./entrypoint.sh
    volumes:
      - ./horilla:/app/horilla
      - ./media:/app/media
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-bullseye
    environment:
      POSTGRES_DB: horilla_saas
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5434:5432"
    restart: unless-stopped
    volumes:
      - horilla-saas-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  horilla-saas-data:
```

### `entrypoint.sh` (updated)

```bash
#!/bin/bash

echo "Waiting for database to be ready..."
python3 manage.py migrate_schemas --shared
python3 manage.py migrate_schemas
python3 manage.py collectstatic --noinput

# Create public tenant if not exists
python3 -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()
from tenants.models import Client, Domain
if not Client.objects.filter(schema_name='public').exists():
    t = Client(schema_name='public', name='Platform', is_active=True, features={})
    t.save()
    Domain.objects.create(domain='localhost', tenant=t, is_primary=True)
    print('Public tenant created')
else:
    print('Public tenant already exists')
"

gunicorn --bind 0.0.0.0:8000 horilla.wsgi:application
```

---

## Step 11: Nginx / Reverse Proxy for Domain Routing

Each customer gets a subdomain (e.g. `acme.hrm.yourplatform.com`). django-tenants detects the tenant from the domain. Point all customer subdomains to the same Django instance.

### Nginx config

```nginx
server {
    listen 80;
    server_name *.hrm.yourplatform.com hrm.yourplatform.com;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }
}
```

Create a wildcard DNS `A` record: `*.hrm.yourplatform.com` → your server IP.

---

## Step 12: Testing the Setup

```bash
# 1. Create a test tenant
python manage.py shell
```

```python
from tenants.models import Client, Domain

t = Client(
    schema_name="testco",
    name="Test Company",
    is_active=True,
    features={"employee": True, "payroll": True, "leave": True},
)
t.save()

Domain.objects.create(
    domain="testco.localhost",
    tenant=t,
    is_primary=True,
)
```

```bash
# 2. Access via subdomain
# Add to /etc/hosts:
# 127.0.0.1 testco.localhost
# Then visit: http://testco.localhost:8010
```

---

## Step 13: Feature Management Admin Portal

The admin panel at `hrm.yourplatform.com/admin/` (public schema) lets you:

1. **Create tenant** — enter company name, generate schema name
2. **Select features** — checkboxes for each HRM module
3. **Set limits** — max employees, subscription expiry
4. **Manage domains** — assign subdomain or custom domain

The `ClientAdmin` in `tenants/admin.py` provides this interface. The `features` JSON field renders as a list of checkboxes. For a better UX, create a custom form widget:

```python
# tenants/forms.py
from django import forms
from .models import Client


class ClientAdminForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert JSON features dict to individual boolean fields
        for slug, label in Client.FEATURES.items():
            self.fields[f"feature_{slug}"] = forms.BooleanField(
                label=label,
                required=False,
                initial=self.instance.features.get(slug, False) if self.instance.pk else False,
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Collect feature flags back into JSON
        features = {}
        for slug in Client.FEATURES:
            features[slug] = self.cleaned_data.get(f"feature_{slug}", False)
        instance.features = features
        if commit:
            instance.save()
        return instance
```

---

## Summary of Required Changes

| Area | Change |
|------|--------|
| **New app** | Create `tenants/` with `Client` and `Domain` models |
| **requirements.txt** | Add `django-tenants` |
| **horilla/settings.py** | Split `INSTALLED_APPS` into `SHARED_APPS` + `TENANT_APPS`, set `TENANT_MODEL`, `DATABASE_ROUTERS`, add `TenantMainMiddleware` |
| **horilla/urls.py** | Split into `urls_public.py` and `urls.py` |
| **horilla/horilla_middlewares.py** | Remove `CompanyMiddleware` registration |
| **horilla/horilla_apps.py** | Remove storages conditional, keep rest |
| **horilla/wsgi.py** | No changes needed (works as-is) |
| **All model files** | Remove `company_id` fields, `HorillaCompanyManager`, `company_filter` |
| **base/horilla_company_manager.py** | Delete |
| **base/middleware.py** | Remove `CompanyMiddleware` class |
| **All serializer files** | Remove `company_id` references |
| **Docker entrypoint** | Use `migrate_schemas` instead of `migrate` |
| **New file** | `tenants/middleware.py` — `FeatureAccessMiddleware` |
| **DNS** | Wildcard `*.hrm.yourplatform.com` → your server |

---

## Rollback Plan

If needed, revert by:

1. Restoring `settings.py` to original `INSTALLED_APPS` (remove split)
2. Re-adding `CompanyMiddleware` to `horilla_middlewares.py`
3. Restoring `base/horilla_company_manager.py`
4. Restoring all `company_id` fields and `HorillaCompanyManager` on models
5. Reverting to `python manage.py migrate` in entrypoint
